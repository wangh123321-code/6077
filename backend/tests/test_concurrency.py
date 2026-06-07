import asyncio
import time
import statistics
from datetime import date, timedelta
from typing import List, Dict, Tuple
import json

import httpx
import pytest

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

TEST_PHONE = "13800000001"
TEST_PASSWORD = "test123456"

TEST_CAT_ROOM_ID = 1
CONCURRENT_USERS = 100
QPS_TARGET = 500
TEST_DURATION = 10


async def get_token(client: httpx.AsyncClient, phone: str, password: str) -> str:
    response = await client.post(
        f"{BASE_URL}{API_PREFIX}/auth/login",
        json={"phone": phone, "password": password}
    )
    data = response.json()
    if data.get("code") == 0:
        return data["data"]["access_token"]
    raise Exception(f"登录失败: {data}")


async def create_booking(
    client: httpx.AsyncClient,
    token: str,
    cat_room_id: int,
    check_in_date: date,
    check_out_date: date,
    user_id: int = 0
) -> Tuple[int, Dict, float]:
    start_time = time.time()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "cat_room_id": cat_room_id,
        "check_in_date": check_in_date.isoformat(),
        "check_out_date": check_out_date.isoformat(),
        "cat_name": f"测试猫_{user_id}",
        "cat_age": 2,
        "addon_services": []
    }
    try:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/bookings",
            json=payload,
            headers=headers,
            timeout=30.0
        )
        elapsed = time.time() - start_time
        return response.status_code, response.json(), elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        return 500, {"error": str(e)}, elapsed


async def register_user(client: httpx.AsyncClient, phone: str, password: str, nickname: str):
    try:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json={"phone": phone, "password": password, "nickname": nickname}
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


async def concurrent_booking_test():
    print("=" * 60)
    print("测试1: 同一猫屋同一时间的并发预订测试")
    print("=" * 60)

    check_in_date = date.today() + timedelta(days=30)
    check_out_date = check_in_date + timedelta(days=2)

    async with httpx.AsyncClient() as client:
        print(f"\n注册测试用户...")
        users = []
        for i in range(CONCURRENT_USERS):
            phone = f"13800{i:06d}"
            result = await register_user(client, phone, "test123456", f"测试用户{i}")
            users.append({"phone": phone, "password": "test123456", "user_id": i})
            if i % 20 == 0:
                print(f"  已注册 {i + 1}/{CONCURRENT_USERS} 用户")

        print(f"\n用户登录获取Token...")
        tokens = []
        for user in users:
            token = await get_token(client, user["phone"], user["password"])
            tokens.append(token)
        print(f"  成功获取 {len(tokens)} 个Token")

        print(f"\n开始并发预订测试 ({CONCURRENT_USERS} 用户预订同一猫屋 {TEST_CAT_ROOM_ID})...")
        print(f"  入住日期: {check_in_date}, 退房日期: {check_out_date}")

        start_time = time.time()
        tasks = [
            create_booking(
                client,
                tokens[i],
                TEST_CAT_ROOM_ID,
                check_in_date,
                check_out_date,
                i
            )
            for i in range(CONCURRENT_USERS)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        success_count = 0
        fail_count = 0
        success_response_times = []
        fail_response_times = []
        conflict_count = 0
        other_errors = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                fail_count += 1
                other_errors.append(f"用户{i}异常: {str(result)}")
                continue

            status_code, data, elapsed = result
            if status_code == 200 and data.get("code") == 0:
                success_count += 1
                success_response_times.append(elapsed)
            else:
                fail_count += 1
                fail_response_times.append(elapsed)
                if data.get("code") == 40009:
                    conflict_count += 1
                else:
                    other_errors.append(f"用户{i}: status={status_code}, code={data.get('code')}, msg={data.get('message')}")

        print("\n" + "-" * 60)
        print(f"测试完成! 总耗时: {total_time:.2f}秒")
        print(f"并发用户数: {CONCURRENT_USERS}")
        print(f"成功预订数: {success_count} (预期: 1)")
        print(f"失败预订数: {fail_count}")
        print(f"  - 并发冲突(预期): {conflict_count}")
        print(f"  - 其他错误: {len(other_errors)}")
        if other_errors:
            for err in other_errors[:5]:
                print(f"    * {err}")

        if success_response_times:
            print(f"\n成功请求响应时间:")
            print(f"  平均: {statistics.mean(success_response_times) * 1000:.2f}ms")
            print(f"  最大: {max(success_response_times) * 1000:.2f}ms")
            print(f"  最小: {min(success_response_times) * 1000:.2f}ms")

        test_passed = success_count == 1 and fail_count == CONCURRENT_USERS - 1
        print("\n" + "=" * 60)
        print(f"测试结果: {'通过' if test_passed else '失败'}")
        print(f"防超订机制验证: {'有效' if success_count == 1 else '失效! 超订发生!'}")
        print("=" * 60 + "\n")

        return test_passed


async def qps_stress_test():
    print("=" * 60)
    print("测试2: 500QPS压力测试")
    print("=" * 60)

    check_in_date = date.today() + timedelta(days=60)
    check_out_date = check_in_date + timedelta(days=1)

    async with httpx.AsyncClient() as client:
        print(f"\n准备测试环境...")
        await register_user(client, TEST_PHONE, TEST_PASSWORD, "压力测试用户")
        token = await get_token(client, TEST_PHONE, TEST_PASSWORD)
        print(f"  测试用户准备完成")

        print(f"\n开始 {QPS_TARGET}QPS 压力测试，持续 {TEST_DURATION} 秒...")

        semaphore = asyncio.Semaphore(QPS_TARGET)
        request_interval = 1.0 / QPS_TARGET

        results = []
        start_time = time.time()
        request_count = 0
        target_requests = QPS_TARGET * TEST_DURATION

        async def bounded_request(req_id):
            async with semaphore:
                cat_room_id = (req_id % 10) + 1
                offset = (req_id // 10) % 100
                ci = check_in_date + timedelta(days=offset)
                co = ci + timedelta(days=1)
                return await create_booking(client, token, cat_room_id, ci, co, req_id)

        print(f"  目标请求数: {target_requests}")
        print(f"  猫屋ID: 1-10 (轮询)")

        tasks = []
        for i in range(target_requests):
            task = asyncio.create_task(bounded_request(i))
            tasks.append(task)
            request_count += 1
            await asyncio.sleep(request_interval * 0.9)

            elapsed = time.time() - start_time
            current_qps = request_count / elapsed if elapsed > 0 else 0
            if i % 500 == 0 and i > 0:
                print(f"  进度: {i}/{target_requests} ({i/target_requests*100:.1f}%), "
                      f"当前QPS: {current_qps:.1f}, 耗时: {elapsed:.1f}s")

        print(f"\n  等待所有请求完成...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time
        actual_qps = len(results) / total_time

        success_count = 0
        fail_count = 0
        exception_count = 0
        response_times = []
        status_counts = {}

        for result in results:
            if isinstance(result, Exception):
                exception_count += 1
                continue

            status_code, data, elapsed = result
            response_times.append(elapsed)

            status_key = f"{status_code}_{data.get('code', 'unknown')}"
            status_counts[status_key] = status_counts.get(status_key, 0) + 1

            if status_code == 200 and data.get("code") == 0:
                success_count += 1
            elif data.get("code") == 40009:
                fail_count += 1
            else:
                fail_count += 1

        print("\n" + "-" * 60)
        print(f"压力测试完成!")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"总请求数: {len(results)}")
        print(f"实际QPS: {actual_qps:.2f} (目标: {QPS_TARGET})")
        print(f"QPS达成率: {actual_qps / QPS_TARGET * 100:.1f}%")
        print(f"\n请求统计:")
        print(f"  成功: {success_count} ({success_count/len(results)*100:.1f}%)")
        print(f"  失败: {fail_count} ({fail_count/len(results)*100:.1f}%)")
        print(f"  异常: {exception_count} ({exception_count/len(results)*100:.1f}%)")

        if response_times:
            rt_sorted = sorted(response_times)
            print(f"\n响应时间统计:")
            print(f"  平均: {statistics.mean(response_times) * 1000:.2f}ms")
            print(f"  中位: {statistics.median(response_times) * 1000:.2f}ms")
            print(f"  P95: {rt_sorted[int(0.95 * len(rt_sorted))] * 1000:.2f}ms")
            print(f"  P99: {rt_sorted[int(0.99 * len(rt_sorted))] * 1000:.2f}ms")
            print(f"  最大: {max(response_times) * 1000:.2f}ms")
            print(f"  最小: {min(response_times) * 1000:.2f}ms")

        print(f"\n状态码分布 (前10):")
        for status, count in sorted(status_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {status}: {count} ({count/len(results)*100:.1f}%)")

        qps_passed = actual_qps >= QPS_TARGET * 0.8
        print("\n" + "=" * 60)
        print(f"QPS测试结果: {'通过' if qps_passed else '未通过'}")
        print(f"  实际QPS {actual_qps:.2f} >= 目标80% {QPS_TARGET * 0.8:.0f}: {qps_passed}")
        print("=" * 60 + "\n")

        return qps_passed


async def multiple_rooms_concurrent_test():
    print("=" * 60)
    print("测试3: 多猫屋并发预订测试")
    print("=" * 60)

    num_rooms = 5
    bookings_per_room = 50

    async with httpx.AsyncClient() as client:
        print(f"\n注册测试用户...")
        users = []
        for i in range(num_rooms * bookings_per_room):
            phone = f"13900{i:06d}"
            await register_user(client, phone, "test123456", f"多房间用户{i}")
            users.append({"phone": phone, "password": "test123456"})

        print(f"用户登录...")
        tokens = []
        for user in users:
            token = await get_token(client, user["phone"], user["password"])
            tokens.append(token)

        print(f"\n开始多猫屋并发测试...")
        print(f"  猫屋数量: {num_rooms}")
        print(f"  每猫屋预订请求: {bookings_per_room}")
        print(f"  总请求数: {num_rooms * bookings_per_room}")

        base_date = date.today() + timedelta(days=90)
        tasks = []
        user_idx = 0

        for room_id in range(1, num_rooms + 1):
            for _ in range(bookings_per_room):
                check_in = base_date + timedelta(days=room_id)
                check_out = check_in + timedelta(days=1)
                tasks.append(create_booking(
                    client, tokens[user_idx], room_id, check_in, check_out, user_idx
                ))
                user_idx += 1

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        room_results = {i: {"success": 0, "fail": 0} for i in range(1, num_rooms + 1)}

        for i, result in enumerate(results):
            room_id = (i // bookings_per_room) + 1
            if isinstance(result, Exception):
                room_results[room_id]["fail"] += 1
                continue

            status_code, data, _ = result
            if status_code == 200 and data.get("code") == 0:
                room_results[room_id]["success"] += 1
            else:
                room_results[room_id]["fail"] += 1

        print(f"\n测试完成! 总耗时: {total_time:.2f}秒")
        print(f"总QPS: {len(results) / total_time:.2f}")
        print("\n各猫屋预订结果:")

        all_passed = True
        for room_id, res in room_results.items():
            passed = res["success"] == 1 and res["fail"] == bookings_per_room - 1
            all_passed = all_passed and passed
            status = "✓" if passed else "✗"
            print(f"  {status} 猫屋{room_id}: 成功={res['success']}, 失败={res['fail']} "
                  f"(预期: 成功=1, 失败={bookings_per_room - 1})")

        print("\n" + "=" * 60)
        print(f"多猫屋测试结果: {'通过' if all_passed else '失败'}")
        print("=" * 60 + "\n")

        return all_passed


async def main():
    print("\n" + "#" * 60)
    print("# 并发测试套件 - 猫咪民宿预订系统")
    print("#" * 60 + "\n")

    test1_passed = await concurrent_booking_test()
    test2_passed = await qps_stress_test()
    test3_passed = await multiple_rooms_concurrent_test()

    print("#" * 60)
    print("# 测试汇总")
    print("#" * 60)
    print(f"1. 单猫屋并发防超订测试: {'通过 ✓' if test1_passed else '失败 ✗'}")
    print(f"2. 500QPS压力测试: {'通过 ✓' if test2_passed else '失败 ✗'}")
    print(f"3. 多猫屋并发测试: {'通过 ✓' if test3_passed else '失败 ✗'}")

    all_passed = test1_passed and test2_passed and test3_passed
    print("\n" + "=" * 60)
    print(f"整体测试结果: {'全部通过 ✓' if all_passed else '存在失败 ✗'}")
    print("=" * 60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
