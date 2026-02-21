from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP
from fastapi import Request
from fastapi.responses import Response, StreamingResponse
import logging

logger = logging.getLogger(__name__)

# Injected into every HTML page to fix i18next async-init timing.
#
# Root cause: i18next uses initAsync:true — actual init is deferred via
# setTimeout(0). React renders before that fires, sees getI18n()=null,
# and falls back to a stub t() that returns raw translation keys.
# Nothing triggers a re-render once translations eventually load.
#
# Fix: synchronously pre-fetch /locales/en/translation.json via XHR in
# <head> (blocking, ~1-5ms on LAN), then intercept window.fetch to return
# a pre-resolved Promise for that URL. When i18next's deferred init runs
# and calls fetch('/locales/en/translation.json'), it gets the data
# instantly (same microtask), finishes initializing before React renders,
# and ready=true from the very first render.
_I18N_FIX = """<script>
localStorage.setItem('i18nextLng','en');
(function(){
  var data=null;
  try{var x=new XMLHttpRequest();x.open('GET','/locales/en/translation.json',false);x.send();if(x.status===200)data=x.responseText;}catch(e){}
  if(!data)return;
  var orig=window.fetch;
  window.fetch=function(){
    var url=arguments[0];
    if(typeof url==='string'&&url.indexOf('/locales/en/translation')!==-1){
      return Promise.resolve(new Response(data,{status:200,headers:{'Content-Type':'application/json'}}));
    }
    return orig.apply(this,arguments);
  };
})();
</script>"""


class OpenHandsWebProxy(BaseProxy):
    def __init__(self, openhands_url: str = None):
        if not openhands_url:
            if IS_CLOUD_RUN:
                openhands_url = f"http://{MAC_SERVER_IP}:3000"
            else:
                openhands_url = "http://127.0.0.1:3000"
        super().__init__(openhands_url)
        logger.info(f"OpenHands Web Proxy initialized: {openhands_url}")

    def get_health_endpoint(self) -> str:
        return "/api/health"

    @property
    def target_url(self) -> str:
        return self.base_url

    async def proxy_request(self, request: Request, path: str) -> StreamingResponse:
        response = await super().proxy_request(request, path)

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        html = body.decode("utf-8", errors="replace")

        if "<head>" in html:
            html = html.replace("<head>", f"<head>{_I18N_FIX}", 1)

        return Response(
            content=html.encode("utf-8"),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type="text/html",
        )


_proxy_instance = None


def get_openhands_proxy() -> OpenHandsWebProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = OpenHandsWebProxy()
    return _proxy_instance
