function log(msg) {
  const el = document.getElementById('log');
  el.textContent = '[' + new Date().toLocaleTimeString() + '] ' + msg + '\n' + el.textContent;
}

document.getElementById('btnConnect').addEventListener('click', async () => {
  log('尝试连接模拟器...');
  try {
    const res = await fetch('/connect', { method: 'POST' });
    const j = await res.json();
    if (!j.ok) {
      alert('连接失败: ' + j.msg);
      log('连接失败: ' + j.msg);
    } else {
      alert('连接成功');
      log('连接成功: ' + j.msg);
    }

    // 如果有详细的命令输出 details，渲染到日志区
    if (j.details) {
      try {
        let lines = [];
        for (const [cmd, info] of Object.entries(j.details)) {
          lines.push('--- ' + cmd + ' ---');
          if (info.rc !== undefined) lines.push('rc: ' + info.rc);
          if (info.out) lines.push('out:\n' + info.out);
          if (info.err) lines.push('err:\n' + info.err);
          lines.push('');
        }
        log(lines.join('\n'));
      } catch (e) {
        console.warn('无法解析 details', e);
      }
    }
  } catch (e) {
    alert('请求 /connect 出错: ' + e);
    log('请求 /connect 出错: ' + e);
  }
});

// load config on page ready
window.addEventListener('DOMContentLoaded', async () => {
  try {
    const r = await fetch('/config');
    const j = await r.json();
    if (j && j.adb_path) document.getElementById('adbPath').value = j.adb_path;
  } catch (e) {
    console.warn('Failed to load config', e);
  }
});

document.getElementById('btnSaveConfig').addEventListener('click', async () => {
  const path = document.getElementById('adbPath').value.trim() || null;
  const res = await fetch('/config', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({adb_path: path}) });
  const j = await res.json();
  if (j.ok) {
    alert('配置已保存');
    log('配置已保存: ' + (j.adb_path || '<none>'));
  } else {
    alert('配置保存失败');
    log('配置保存失败');
  }
});

document.getElementById('btnScreenshot').addEventListener('click', async () => {
  log('抓取屏幕...');
  try {
    const res = await fetch('/screenshot');
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      alert('抓屏失败: ' + (j.msg || res.statusText));
      log('抓屏失败: ' + (j.msg || res.statusText));
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const img = document.getElementById('screenshotImg');
    img.src = url;
    const dl = document.getElementById('btnScreenshotDownload');
    dl.style.display = 'inline-block';
    dl.onclick = () => {
      const a = document.createElement('a');
      a.href = url;
      a.download = 'screenshot.png';
      document.body.appendChild(a);
      a.click();
      a.remove();
    };
    log('抓屏成功');
  } catch (e) {
    alert('抓屏出错: ' + e);
    log('抓屏出错: ' + e);
  }
});

document.getElementById('btnStart').addEventListener('click', async () => {
  log('发送启动命令...');
  const res = await fetch('/start', { method: 'POST' });
  const j = await res.json();
  alert(j.msg);
  log('启动: ' + j.msg);
});

document.getElementById('btnStop').addEventListener('click', async () => {
  log('发送停止命令...');
  const res = await fetch('/stop', { method: 'POST' });
  const j = await res.json();
  alert(j.msg);
  log('停止: ' + j.msg);
});
