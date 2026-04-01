from typing import Any

import requests
from bs4 import BeautifulSoup
from rest_framework import generics, status
from rest_framework.response import Response


class SwimLoginView(generics.GenericAPIView):
    def __init__(self):
        super().__init__()
        self.request_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        }
        self.session = requests.Session()

    def post(self, request, *args, **kwargs) -> Response:
        is_logged_in = self.get_authenticated_session()
        if not is_logged_in:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        base_url = "https://demirandabad.amsterdam.nl/Exhibitions/Overview"
        response = self.session.get(
            base_url,
            params=request.query_params,
            headers=self.request_headers,
            timeout=10,
        )

        soup = BeautifulSoup(response.text, "html.parser")
        soup.find_all(class_="productName")
        return Response({"login_succeeded": is_logged_in}, status=status.HTTP_200_OK)

    def get_authenticated_session(self) -> bool:
        base_url = "https://demirandabad.amsterdam.nl/Home"
        params = {
            "shop": "1D5655F0-713F-47FB-80F0-F823C1E6C2BC",
        }
        post_body, referer_url = self.get_payload(base_url, params)
        self.make_login_post(base_url, params, post_body, referer_url)

        is_logged_in = self.check_is_logged_in()
        return is_logged_in

    def get_payload(self, base_url: str, params: dict[str, str]):
        resp = self.session.get(
            base_url, params=params, headers=self.request_headers, timeout=10
        )
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        payload: dict[str, str] = {}

        check_fields = [
            "__EVENTTARGET",
            "__EVENTARGUMENT",
            "__LASTFOCUS",
            "__VIEWSTATE",
            "__VIEWSTATEGENERATOR",
            "__SCROLLPOSITIONX",
            "__SCROLLPOSITIONY",
            "__VIEWSTATEENCRYPTED",
            "__PREVIOUSPAGE",
            "__EVENTVALIDATION",
            "__RequestVerificationToken",
        ]
        for el in soup.find_all("input"):
            name = el.get("name")
            if name in check_fields:
                payload[name] = el.get("value", "")
        return payload, resp.url

    def make_login_post(
        self,
        base_url: str,
        params: dict[str, str],
        payload: dict[str, str | Any],
        referer_url: str,
    ) -> None:
        payload.update(
            {
                "ctl00$MainContent$ctlLoginWidget$txtUsername": "jonathanjeroen",
                "ctl00$MainContent$ctlLoginWidget$txtPassword": PASSWORD,
                "ctl00$MainContent$ctlLoginWidget$chkRememberMe": "on",
                "ctl00$MainContent$ctlLoginWidget$btnLogin": "Inloggen",
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__LASTFOCUS": "",
                "__ASYNCPOST": "true",
                "ctl00$RadScriptManager": "ctl00$MainContent$ctlLoginWidget$LoadPanel|ctl00$MainContent$ctlLoginWidget$btnLogin",
            }
        )
        headers_post = {
            "User-Agent": self.request_headers["User-Agent"],
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "X-MicrosoftAjax": "Delta=true",
            "Origin": "https://demirandabad.amsterdam.nl",
            "Referer": referer_url,
        }
        response = self.session.post(
            base_url, params=params, data=payload, headers=headers_post, timeout=10
        )
        print(response.text)

    def check_is_logged_in(self: dict[str, str]) -> bool:
        check_response = self.session.get(
            "https://demirandabad.amsterdam.nl/Home",
            params={"shop": "1D5655F0-713F-47FB-80F0-F823C1E6C2BC"},
            headers=self.request_headers,
            timeout=10,
        )
        html = check_response.text
        is_logged_in = "Welkom Jeroen Beekman" in html
        return is_logged_in


PASSWORD = "Klokhuiswater1!"
