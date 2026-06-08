import logging
import os
import subprocess
import asyncio
import gzip
import shutil
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.config.settings import settings
from app.core.errors import BusinessException, ErrorCode

logger = logging.getLogger(__name__)


class BackupService:
    """数据库备份服务类，使用pg_dump执行备份，支持压缩和S3上传"""

    def __init__(self):
        self.backup_dir = Path(settings.BACKUP_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = settings.BACKUP_RETENTION_DAYS
        self.compress = settings.BACKUP_COMPRESS
        self.prefix = settings.BACKUP_PREFIX
        self.upload_s3 = settings.BACKUP_UPLOAD_S3
        self.s3_bucket = settings.BACKUP_S3_BUCKET
        self.s3_prefix = settings.BACKUP_S3_PREFIX

        if self.upload_s3:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=os.getenv('S3_ENDPOINT_URL'),
                aws_access_key_id=os.getenv('S3_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('S3_SECRET_ACCESS_KEY'),
                region_name=os.getenv('S3_REGION', 'us-east-1')
            )
        else:
            self.s3_client = None

    def _get_backup_filename(self, timestamp: Optional[datetime] = None) -> str:
        """
        生成备份文件名

        Args:
            timestamp: 时间戳，默认当前时间

        Returns:
            备份文件名
        """
        if timestamp is None:
            timestamp = datetime.now()
        date_str = timestamp.strftime('%Y%m%d_%H%M%S')
        ext = '.sql.gz' if self.compress else '.sql'
        return f"{self.prefix}_{date_str}{ext}"

    def _get_backup_path(self, filename: str) -> Path:
        """
        获取备份文件完整路径

        Args:
            filename: 文件名

        Returns:
            完整路径
        """
        return self.backup_dir / filename

    async def create_backup(self) -> Dict[str, Any]:
        """
        创建数据库备份

        Returns:
            备份结果信息字典

        Raises:
            BusinessException: 备份失败时抛出
        """
        timestamp = datetime.now()
        filename = self._get_backup_filename(timestamp)
        backup_path = self._get_backup_path(filename)

        logger.info(f"开始创建数据库备份: {backup_path}")

        try:
            await asyncio.to_thread(self._execute_pg_dump, backup_path)

            file_size = backup_path.stat().st_size
            logger.info(f"备份文件创建成功: {backup_path}, 大小: {file_size} bytes")

            s3_url = None
            if self.upload_s3 and self.s3_client:
                s3_url = await self._upload_to_s3(backup_path, filename)
                logger.info(f"备份文件已上传到S3: {s3_url}")

            await self._cleanup_old_backups()

            return {
                "filename": filename,
                "filepath": str(backup_path),
                "size": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "timestamp": timestamp.isoformat(),
                "compressed": self.compress,
                "s3_url": s3_url,
                "uploaded": s3_url is not None
            }

        except subprocess.CalledProcessError as e:
            error_msg = f"pg_dump执行失败: {e.stderr}"
            logger.error(error_msg)
            if backup_path.exists():
                backup_path.unlink()
            raise BusinessException(
                code=ErrorCode.DATABASE_ERROR,
                message="数据库备份失败",
                data={"error": error_msg}
            )
        except Exception as e:
            error_msg = f"备份创建失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if backup_path.exists():
                backup_path.unlink()
            raise BusinessException(
                code=ErrorCode.DATABASE_ERROR,
                message="数据库备份失败",
                data={"error": error_msg}
            )

    def _execute_pg_dump(self, backup_path: Path) -> None:
        """
        执行pg_dump命令（同步方法，在独立线程中运行）

        Args:
            backup_path: 备份文件路径

        Raises:
            subprocess.CalledProcessError: 命令执行失败
        """
        env = os.environ.copy()
        env['PGPASSWORD'] = settings.DB_PASSWORD

        pg_dump_cmd = [
            'pg_dump',
            f'--host={settings.DB_HOST}',
            f'--port={settings.DB_PORT}',
            f'--username={settings.DB_USER}',
            f'--dbname={settings.DB_NAME}',
            '--format=plain',
            '--encoding=UTF8',
            '--no-owner',
            '--no-acl',
            '--disable-triggers'
        ]

        if self.compress:
            with open(backup_path, 'wb') as f:
                pg_dump_proc = subprocess.Popen(
                    pg_dump_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=False
                )
                gzip_proc = subprocess.Popen(
                    ['gzip', '-c'],
                    stdin=pg_dump_proc.stdout,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=False
                )
                pg_dump_proc.stdout.close()

                _, pg_dump_stderr = pg_dump_proc.communicate()
                _, gzip_stderr = gzip_proc.communicate()

                if pg_dump_proc.returncode != 0:
                    raise subprocess.CalledProcessError(
                        pg_dump_proc.returncode,
                        pg_dump_cmd,
                        stderr=pg_dump_stderr.decode()
                    )
                if gzip_proc.returncode != 0:
                    raise subprocess.CalledProcessError(
                        gzip_proc.returncode,
                        ['gzip'],
                        stderr=gzip_stderr.decode()
                    )
        else:
            result = subprocess.run(
                pg_dump_cmd,
                stdout=open(backup_path, 'w'),
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode,
                    pg_dump_cmd,
                    stderr=result.stderr
                )

    async def _upload_to_s3(self, file_path: Path, s3_key: str) -> str:
        """
        上传备份文件到S3

        Args:
            file_path: 本地文件路径
            s3_key: S3对象键

        Returns:
            S3文件URL

        Raises:
            BusinessException: 上传失败
        """
        full_s3_key = f"{self.s3_prefix}{s3_key}"

        try:
            await asyncio.to_thread(
                self.s3_client.upload_file,
                str(file_path),
                self.s3_bucket,
                full_s3_key
            )

            return f"s3://{self.s3_bucket}/{full_s3_key}"

        except ClientError as e:
            error_msg = f"S3上传失败: {str(e)}"
            logger.error(error_msg)
            raise BusinessException(
                code=ErrorCode.DATABASE_ERROR,
                message="备份文件上传到S3失败",
                data={"error": error_msg, "s3_key": full_s3_key}
            )

    async def _cleanup_old_backups(self) -> None:
        """清理超过保留天数的本地备份文件"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0
        saved_space = 0

        try:
            for file_path in self.backup_dir.glob(f"{self.prefix}_*"):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_count += 1
                        saved_space += file_size
                        logger.info(f"删除过期备份文件: {file_path}")

            if deleted_count > 0:
                logger.info(
                    f"清理完成，删除 {deleted_count} 个过期备份文件，"
                    f"释放空间: {saved_space / (1024 * 1024):.2f} MB"
                )

        except Exception as e:
            logger.error(f"清理过期备份文件失败: {str(e)}", exc_info=True)

    async def list_backups(self) -> List[Dict[str, Any]]:
        """
        列出所有本地备份文件

        Returns:
            备份文件列表
        """
        backups = []

        for file_path in sorted(self.backup_dir.glob(f"{self.prefix}_*"), reverse=True):
            if file_path.is_file():
                stat = file_path.stat()
                backups.append({
                    "filename": file_path.name,
                    "filepath": str(file_path),
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        return backups

    async def restore_backup(self, filename: str) -> Dict[str, Any]:
        """
        从备份文件恢复数据库

        Args:
            filename: 备份文件名

        Returns:
            恢复结果信息

        Raises:
            BusinessException: 恢复失败
        """
        backup_path = self._get_backup_path(filename)

        if not backup_path.exists():
            raise BusinessException(
                code=ErrorCode.NOT_FOUND,
                message=f"备份文件不存在: {filename}"
            )

        logger.warning(f"开始从备份恢复数据库: {backup_path}")

        try:
            await asyncio.to_thread(self._execute_restore, backup_path)

            logger.info(f"数据库恢复成功: {backup_path}")

            return {
                "filename": filename,
                "filepath": str(backup_path),
                "restored_at": datetime.now().isoformat(),
                "success": True
            }

        except subprocess.CalledProcessError as e:
            error_msg = f"psql执行失败: {e.stderr}"
            logger.error(error_msg)
            raise BusinessException(
                code=ErrorCode.DATABASE_ERROR,
                message="数据库恢复失败",
                data={"error": error_msg}
            )
        except Exception as e:
            error_msg = f"恢复失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise BusinessException(
                code=ErrorCode.DATABASE_ERROR,
                message="数据库恢复失败",
                data={"error": error_msg}
            )

    def _execute_restore(self, backup_path: Path) -> None:
        """
        执行psql恢复命令（同步方法）

        Args:
            backup_path: 备份文件路径

        Raises:
            subprocess.CalledProcessError: 命令执行失败
        """
        env = os.environ.copy()
        env['PGPASSWORD'] = settings.DB_PASSWORD

        psql_cmd = [
            'psql',
            f'--host={settings.DB_HOST}',
            f'--port={settings.DB_PORT}',
            f'--username={settings.DB_USER}',
            f'--dbname={settings.DB_NAME}',
            '--set=ON_ERROR_STOP=1'
        ]

        if str(backup_path).endswith('.gz'):
            with gzip.open(backup_path, 'rb') as f:
                psql_proc = subprocess.Popen(
                    psql_cmd,
                    stdin=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=False
                )
                _, stderr = psql_proc.communicate(input=f.read())

                if psql_proc.returncode != 0:
                    raise subprocess.CalledProcessError(
                        psql_proc.returncode,
                        psql_cmd,
                        stderr=stderr.decode()
                    )
        else:
            with open(backup_path, 'r') as f:
                psql_proc = subprocess.Popen(
                    psql_cmd,
                    stdin=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )
                _, stderr = psql_proc.communicate(input=f.read())

                if psql_proc.returncode != 0:
                    raise subprocess.CalledProcessError(
                        psql_proc.returncode,
                        psql_cmd,
                        stderr=stderr
                    )

    async def delete_backup(self, filename: str) -> Dict[str, Any]:
        """
        删除备份文件

        Args:
            filename: 备份文件名

        Returns:
            删除结果信息
        """
        backup_path = self._get_backup_path(filename)

        if not backup_path.exists():
            raise BusinessException(
                code=ErrorCode.NOT_FOUND,
                message=f"备份文件不存在: {filename}"
            )

        try:
            file_size = backup_path.stat().st_size
            backup_path.unlink()

            logger.info(f"备份文件已删除: {backup_path}")

            return {
                "filename": filename,
                "filepath": str(backup_path),
                "size": file_size,
                "deleted_at": datetime.now().isoformat()
            }

        except Exception as e:
            error_msg = f"删除备份文件失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise BusinessException(
                code=ErrorCode.DATABASE_ERROR,
                message="删除备份文件失败",
                data={"error": error_msg}
            )


backup_service = BackupService()
