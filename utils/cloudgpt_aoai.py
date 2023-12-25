
import datetime
from typing import Literal, Optional


def get_openai_token(
    token_cache_file: str = 'cloudgpt-apim-token-cache.bin',
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> str:
    '''
    acquire token from Azure AD for CloudGPT OpenAI

    Parameters
    ----------
    token_cache_file : str, optional
        path to the token cache file, by default 'cloudgpt-apim-token-cache.bin' in the current directory
    client_id : Optional[str], optional
        client id for AAD app, by default None
    client_secret : Optional[str], optional
        client secret for AAD app, by default None

    Returns
    -------
    str
        access token for CloudGPT OpenAI
    '''
    import msal
    import os

    cache = msal.SerializableTokenCache()

    def save_cache():
        if token_cache_file is not None and cache.has_state_changed:
            with open(token_cache_file, "w") as cache_file:
                cache_file.write(cache.serialize())
    if os.path.exists(token_cache_file):
        cache.deserialize(open(token_cache_file, "r").read())

    authority = "https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47"
    api_scope_base = "api://feb7b661-cac7-44a8-8dc1-163b63c23df2"

    if client_id is not None and client_secret is not None:
        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority,
            token_cache=cache
        )
        result = app.acquire_token_for_client(
            scopes=[
                api_scope_base + "/.default",
            ])
        if "access_token" in result:
            return result['access_token']
        else:
            print(result.get("error"))
            print(result.get("error_description"))
            raise Exception(
                "Authentication failed for acquiring AAD token for CloudGPT OpenAI")

    scopes = [api_scope_base + "/openai"]
    app = msal.PublicClientApplication(
        "feb7b661-cac7-44a8-8dc1-163b63c23df2",
        authority=authority,
        token_cache=cache
    )
    result = None
    for account in app.get_accounts():
        try:
            result = app.acquire_token_silent(scopes, account=account)
            if result is not None and "access_token" in result:
                save_cache()
                return result['access_token']
            result = None
        except Exception:
            continue

    accounts_in_cache = cache.find(msal.TokenCache.CredentialType.ACCOUNT)
    for account in accounts_in_cache:
        try:
            refresh_token = cache.find(
                msal.CredentialType.REFRESH_TOKEN,
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
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
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
    openai.api_key = get_openai_token(
        client_id=client_id, client_secret=client_secret)
    response = openai.ChatCompletion.create(
        engine=engine,
        *args,
        **kwargs
    )
    return response


def auto_refresh_token(
    token_cache_file: str = 'cloudgpt-apim-token-cache.bin',
    interval: datetime.timedelta = datetime.timedelta(minutes=15),
    on_token_update: callable = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
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
        openai.api_key = get_openai_token(
            token_cache_file=token_cache_file,
            client_id=client_id,
            client_secret=client_secret,
        )

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


def test_get_chat_completion():
    def test_call(*args, **kwargs):
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
            stop=None,
            *args,
            **kwargs
        )

        print(response['choices'][0]['message'])

    print("test without AAD app")
    test_call()  # test without AAD app

    import os
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')

    if client_id is None or client_secret is None:
        print("please set CLIENT_ID and CLIENT_SECRET environment variables for testing AAD app")
    else:
        print("test with AAD app")
        # test with AAD app
        test_call(client_id=client_id, client_secret=client_secret)


if __name__ == "__main__":
    prompt="""Given a question and a set of relations, select necessary relations to build reasoning paths of the question. A question can have multiple reasoning paths (to form a reasoning graph):
Q: Find the person who said \"Taste cannot be controlled by law\", where did this person die from?
Relation set: 'people.person.quotations'
'people.person.quotationsbook_id'
 'people.person.children'
 'people.person.religion'
 'people.person.date_of_birth'
 'people.deceased_person.place_of_death'
 'people.deceased_person.cause_of_death'
 'people.deceased_person.place_of_burial'
 'people.deceased_person.date_of_death'
 'people.deceased_person.place_of_cremation'
 'media_common.quotation.author'
 'media_common.quotation.source'
 'media_common.quotation_source.quotations'
 'media_common.quotation_addressee.quotations'
Reasoning Path: \"Taste cannot be controlled by law\" -- people.person.quotations -- people.deceased_person.place_of_death
\"Taste cannot be controlled by law\" -- media_common.quotation_source.quotations -- people.deceased_person.place_of_death

Q: The artist nominated for The Long Winter lived where?
Relation set: 'book.written_work.author'
'book.author.works_written'
'award.long_list_nomination.nominated_work'
'award.long_listed_work.long_list_nominations'
'book.written_work.date_written'
'people.person.places_lived'
'people.place_lived.person'
'people.place_lived.location'
'people.place_lived.start_date'
'people.place_lived.end_date'
'award.long_list_nominee.long_list_nominations'
'award.long_list_nomination.nominee'
'award.long_list_nomination.award'
'award.award_nominee.award_nominations'
'award.award_nomination.award_nominee'
'award.long_list_nomination.year'
Reasoning Path: The Long Winter -- book.written_work.author -- people.person.places_lived -- people.place_lived.location
The Long Winter -- award.long_list_nomination.nominee -- people.person.places_lived -- people.place_lived.location
The Long Winter -- award.long_list_nomination.nominee -- people.place_lived.location

Q: The movie featured Miley Cyrus and was produced by Tobin Armbrust?
Relation set: 'film.film_featured_song.featured_in_film'
'film.producer.films_executive_produced'
'film.film.starring'
'film.film_location.featured_in_films'
'film.film.featured_film_locations'
'film.producer.films_executive_produced'
'film.film.executive_produced_by'
'film.film.produced_by'
'film.producer.film'
'film.film_featured_song.featured_in_film'
'film.performance.actor'
'film.actor.dubbing_performances'
'film.film_featured_song.performed_by'
Reasoning Path: Miley Cyrus -- film.film.starring
Tobin Armbrust -- film.producer.films_executive_produced
Miley Cyrus -- film.performance.actor
Tobin Armbrust -- film.producer.film
Tobin Armbrust -- film.film.executive_produced_by
Tobin Armbrust -- film.film.produced_by

Question: What country bordering France contains an airport that serves Nijmegen?
Relation Set:'location.location.containedby'
'location.location.partially_containedby'
'location.location.nearby_airports'
'location.location.primarily_containedby'
'location.location.contains'
'freebase.theme.module_border_color'
'astronomy.constellation_bordering_relationship.constellations'
'astronomy.constellation.bordering_constellations_new'
'user.jdouglas.config.theme.module_border_color'
'base.services.airport_shuttle_service.airports_served'
'aviation.airport.serves'
'aviation.airline.airports_served'
'aviation.airline_airport_presence.cities_served'
'location.location.adjoin_s'
'location.adjoining_relationship.adjoins'
'base.infrastructure.sewage_treatment_plant.serves_location_s'
Reasoning path:"""
    test_get_chat_completion(prompt)
