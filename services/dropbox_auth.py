import dropbox

APP_KEY = "yx9dmhh1h29m2xt"
APP_SECRET = "q6w9b5expshg4vg"

oauth_flow = dropbox.DropboxOAuth2FlowNoRedirect(
    APP_KEY, APP_SECRET, token_access_type='offline'
)
authorize_url = oauth_flow.start()
print("Vai a:", authorize_url)
code = input("Incolla il codice qui: ").strip()
res = oauth_flow.finish(code)

print("ACCESS TOKEN =", res.access_token)
print("REFRESH TOKEN =", res.refresh_token)
