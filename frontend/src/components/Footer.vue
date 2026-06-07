<template>
  <footer class="app-footer">
    <div class="footer-container">
      <div class="footer-content">
        <div class="footer-section">
          <h3>关于我们</h3>
          <p>专业的猫咪酒店，为您的爱宠提供温馨舒适的住宿环境。</p>
        </div>
        <div class="footer-section">
          <h3>联系方式</h3>
          <p>电话：400-123-4567</p>
          <p>邮箱：service@cathotel.com</p>
          <p>地址：北京市朝阳区猫咪大道88号</p>
        </div>
        <div class="footer-section">
          <h3>营业时间</h3>
          <p>周一至周日：09:00 - 21:00</p>
          <p>节假日：10:00 - 18:00</p>
        </div>
        <div class="footer-section">
          <h3>关注我们</h3>
          <div class="qrcode">
            <img src="https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=simple%20QR%20code&image_size=square" alt="公众号二维码" />
            <p>扫码关注公众号</p>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <p>&copy; {{ year }} 猫咪酒店管理系统 版权所有</p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
const year = new Date().getFullYear()
</script>

<style scoped lang="scss">
.app-footer {
  background: #2c3e50;
  color: #ecf0f1;
  padding: 48px 0 24px;

  .footer-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .footer-content {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 48px;
    padding-bottom: 32px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);

    @media (max-width: 768px) {
      grid-template-columns: repeat(2, 1fr);
      gap: 24px;
    }
  }

  .footer-section {
    h3 {
      font-size: 16px;
      margin-bottom: 16px;
      color: #fff;
    }

    p {
      font-size: 14px;
      line-height: 1.8;
      color: #bdc3c7;
      margin: 8px 0;
    }

    .qrcode {
      img {
        width: 100px;
        height: 100px;
        background: #fff;
        padding: 8px;
        border-radius: 8px;
      }

      p {
        margin-top: 8px;
        font-size: 12px;
      }
    }
  }

  .footer-bottom {
    padding-top: 24px;
    text-align: center;

    p {
      font-size: 14px;
      color: #95a5a6;
      margin: 0;
    }
  }
}
</style>
