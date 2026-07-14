const localtunnel = require('localtunnel');

(async () => {
  try {
    console.log('正在启动 localtunnel，连接到本地 80 端口...');

    const tunnel = await localtunnel({
      port: 80,
      // subdomain: 'dify-travel' // 如果需要固定域名，取消注释
    });

    console.log('\n✅ 隧道已成功建立！');
    console.log('='.repeat(60));
    console.log(`公网访问地址: ${tunnel.url}`);
    console.log('='.repeat(60));
    console.log('\n📋 配置飞书事件订阅时使用以下 URL:');
    console.log(`${tunnel.url}/console/api/workspaces/current/data-source/feishu/event`);
    console.log('\n按 Ctrl+C 停止隧道');
    console.log('\n保持此窗口运行，隧道将持续可用...\n');

    // 监听关闭事件
    tunnel.on('close', () => {
      console.log('隧道已关闭');
    });

    // 监听错误事件
    tunnel.on('error', (err) => {
      console.error('隧道错误:', err);
    });

    // 保持进程运行
    process.on('SIGINT', () => {
      console.log('\n正在关闭隧道...');
      tunnel.close();
      process.exit(0);
    });

  } catch (err) {
    console.error('❌ 启动失败:', err.message);
    process.exit(1);
  }
})();
