"""兼容适配器 — 让使用 sync_playwright() 的代码无缝切换到 CloakBrowser。

用法:
    from cloak_compat import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, ...)
        # ... 其余代码不变
"""

try:
    from cloakbrowser import launch as _cloak_launch
    _HAS_CLOAK = True
except ImportError:
    _HAS_CLOAK = False

from cloak_compat import sync_playwright as _real_sync_playwright


class _CloakBrowserProxy:
    """模拟 p.chromium 的接口，底层用 CloakBrowser。"""
    def __init__(self, **default_opts):
        self._default_opts = default_opts

    def launch(self, headless=True, args=None, proxy=None, env=None, **kwargs):
        opts = {**self._default_opts, "headless": headless, "humanize": True}
        if proxy:
            if isinstance(proxy, dict):
                opts["proxy"] = proxy.get("server", "")
            else:
                opts["proxy"] = proxy
        # args, env 等 CloakBrowser 不需要的参数静默忽略
        return _cloak_launch(**opts)

    def connect_over_cdp(self, url):
        # CloakBrowser 不支持 CDP 连接，回退到真实 Playwright
        pw = _real_sync_playwright().start()
        return pw.chromium.connect_over_cdp(url)

    def launch_persistent_context(self, user_data_dir, **kwargs):
        # CloakBrowser 不支持 persistent context，回退到真实 Playwright
        pw = _real_sync_playwright().start()
        return pw.chromium.launch_persistent_context(user_data_dir, **kwargs)


class _CloakPlaywright:
    """模拟 sync_playwright() 返回的对象。"""
    def __init__(self):
        self.chromium = _CloakBrowserProxy()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def start(self):
        return self

    def stop(self):
        pass


def sync_playwright():
    """兼容 drop-in 替换。有 CloakBrowser 用 CloakBrowser，否则回退。"""
    if _HAS_CLOAK:
        return _CloakPlaywright()
    return _real_sync_playwright()
