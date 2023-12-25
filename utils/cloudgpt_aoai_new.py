
import datetime
from typing import Literal


def get_openai_token(token_cache_file: str = 'cloudgpt-apim-token-cache.bin') -> str:
    '''
    acquire token from Azure AD for CloudGPT OpenAI

    Parameters
    ----------
    token_cache : str, optional
        path to the token cache file, by default 'cloudgpt-apim-token-cache.bin' in the current directory

    Returns
    -------
    str
        access token for CloudGPT OpenAI
    '''
    import msal
    import os

    cache = msal.SerializableTokenCache()

    def save_cache():
        if cache.has_state_changed:
            with open(token_cache_file, "w") as cache_file:
                cache_file.write(cache.serialize())
    if os.path.exists(token_cache_file):
        cache.deserialize(open(token_cache_file, "r").read())

    scopes = ["api://feb7b661-cac7-44a8-8dc1-163b63c23df2/openai"]
    app = msal.PublicClientApplication(
        "feb7b661-cac7-44a8-8dc1-163b63c23df2",
        authority="https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47",
        token_cache=cache
    )
    result = None
    try:
        account = app.get_accounts()[0]
        result = app.acquire_token_silent(scopes, account=account)
        if result is not None and "access_token" in result:
            save_cache()
            return result['access_token']
        result = None
    except Exception:
        pass

    try:
        account = cache.find(cache.CredentialType.ACCOUNT)[0]
        refresh_token = cache.find(
            cache.CredentialType.REFRESH_TOKEN,
            query={
                "home_account_id": account["home_account_id"]
            })[0]
        result = app.acquire_token_by_refresh_token(
            refresh_token["secret"], scopes=scopes)
        if result is not None and "access_token" in result:
            save_cache()
            return result['access_token']
        result = None
    except Exception:
        pass

    if result is None:
        print("no token available from cache, acquiring token from AAD")
        # The pattern to acquire a token looks like this.
        flow = app.initiate_device_flow(scopes=scopes)
        print(flow['message'])
        result = app.acquire_token_by_device_flow(flow=flow)
        if result is not None and "access_token" in result:
            save_cache()
            return result['access_token']
        else:
            print(result.get("error"))
            print(result.get("error_description"))
            raise Exception(
                "Authentication failed for acquiring AAD token for CloudGPT OpenAI")


cloudgpt_available_models = Literal[
    "gpt-35-turbo-20220309",
    "gpt-35-turbo-16k-20230613",
    "gpt-35-turbo-20230613",

    "gpt-4-20230321",
    "gpt-4-32k-20230321"
]


def get_chat_completion(
    engine: cloudgpt_available_models,
    *args,
    **kwargs
):
    """
    helper function for getting chat completion from CloudGPT OpenAI
    """
    import openai
    openai.api_type = "azure"
    openai.api_base = "https://cloudgpt-openai.azure-api.net/"
    openai.api_version = "2023-07-01-preview"
    # to maintain token freshness, we need to acquire a new token every time we use the API
    openai.api_key = get_openai_token()
    response = openai.ChatCompletion.create(
        engine=engine,
        *args,
        **kwargs
    )
    return response



def get_embedding(
    *args,
    **kwargs
):
    """
    helper function for getting chat completion from CloudGPT OpenAI
    """
    import openai
    openai.api_type = "azure"
    openai.api_base = "https://cloudgpt-openai.azure-api.net/"
    openai.api_version = "2023-07-01-preview"
    # to maintain token freshness, we need to acquire a new token every time we use the API
    openai.api_key = get_openai_token()
    
    response = openai.Embedding.create(engine="text-embedding-ada-002",
                                       *args,
                                       **kwargs)
    return response['data'][0]['embedding']



def auto_refresh_token(
    token_cache_file: str = 'cloudgpt-apim-token-cache.bin',
    interval: datetime.timedelta = datetime.timedelta(minutes=15),
    on_token_update: callable = None
) -> callable:
    """
    helper function for auto refreshing token from CloudGPT OpenAI

    Parameters
    ----------
    token_cache_file : str, optional
        path to the token cache file, by default 'cloudgpt-apim-token-cache.bin' in the current directory
    interval : datetime.timedelta, optional
        interval for refreshing token, by default 15 minutes
    on_token_update : callable, optional
        callback function to be called when token is updated, by default None. In the callback function, you can get token from openai.api_key

    Returns
    -------
    callable
        a callable function that can be used to stop the auto refresh thread
    """

    import threading

    def update_token():
        import openai

        openai.api_type = "azure"
        openai.api_base = "https://cloudgpt-openai.azure-api.net/"
        openai.api_version = "2023-07-01-preview"
        openai.api_key = get_openai_token(token_cache_file)

        if on_token_update is not None:
            on_token_update()

    def refresh_token_thread():
        import time
        while True:
            try:
                update_token()
            except Exception as e:
                print("failed to acquire token from AAD for CloudGPT OpenAI", e)
            time.sleep(interval.total_seconds())

    try:
        update_token()
    except Exception as e:
        raise Exception(
            "failed to acquire token from AAD for CloudGPT OpenAI", e)

    thread = threading.Thread(target=refresh_token_thread, daemon=True)
    thread.start()

    def stop():
        thread.stop()

    return stop


if __name__ == '__main__':
    test_message = "What is the content?"
    test_chat_message = [{"role": "user", "content": test_message}]
    response = get_chat_completion(
        engine="gpt-35-turbo-20220309",
        messages=test_chat_message,
        temperature=0.7,
        max_tokens=100,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    print(get_embedding(input=test_message))
    print(response['choices'][0]['message'])
