from rest_framework.decorators import api_view
from rest_framework.response import Response

APP_LINKS={
    "parking": "https://www.amsterdam.nl/parkeren/",
    "parking_visitors" : "https://aanmeldenparkeren.amsterdam.nl/login",
    "documents" : "https://www.amsterdam.nl/burgerzaken/akten-uittreksels/",
    "relocation" : "https://www.amsterdam.nl/burgerzaken/verhuizing-doorgeven/",
    "income_help" : "https://www.amsterdam.nl/werk-inkomen/hulp-bij-laag-inkomen/",
    "citypass" : "https://www.amsterdam.nl/stadspas/",
    "cityPassRequest": "https://formulieren.amsterdam.nl/TriplEforms/DirectRegelen/formulier/nl-NL/evAmsterdam/HulpBijLaagInkomen.aspx",
    "cityPassChildBudget": "https://www.amsterdam.nl/stadspas/kindtegoed/",
    "cityPassUsage": "https://www.amsterdam.nl/stadspas/werkt-stadspas/",
    "acknowledgeChild": "https://www.amsterdam.nl/veelgevraagd/een-kind-erkennen-b0bd7",
    "birth": "https://www.amsterdam.nl/burgerzaken/geboorte-erkenning-kinderen/geboorteaangifte/",
    "immigration": "https://www.amsterdam.nl/burgerzaken/immigratie",
    "lifelessBirth": "https://www.amsterdam.nl/veelgevraagd/levenloos-geboren-kindje-registreren-in-de-brp-daaf8#case_%7BB104B52F-9A3B-4923-8B5D-1FA60B6F3591%7D",
    "marriage": "https://www.amsterdam.nl/burgerzaken/trouwen-en-partnerschap/",
    "marriagePermission": "https://www.amsterdam.nl/veelgevraagd/verklaring-van-huwelijksbevoegdheid-9fedd#case_%7B0F588CAC-30A3-4ED1-B355-10F9EE8759D9%7D",
    "naturalisation": "https://www.amsterdam.nl/burgerzaken/naturalisatie",
    "passing": "https://www.amsterdam.nl/burgerzaken/overlijden/aangifte-overlijden/",
    "passingForFuneralDirectors": "https://www.amsterdam.nl/burgerzaken/overlijden/aangifte-overlijden-uitvaartondernemers/",
    "makeAppointMentWeesp": "https://formulieren.amsterdam.nl/TriplEforms/DirectRegelen/formulier/nl-NL/evAmsterdam/afspraakmakenweesp.aspx",
    "contactForm": "https://formulieren.amsterdam.nl/TriplEforms/DirectRegelen/formulier/nl-NL/evAmsterdam/Contactformulier.aspx",
    "feedbackForm": "https://formulier.amsterdam.nl/thema/burgerzaken/amsterdam-app/Uw-mening/",
    "elections": "https://www.amsterdam.nl/verkiezingen/"
}

@api_view(["GET"])
def get_links(request):
    """
    Return the app links
    """
    return Response(APP_LINKS,status=200)
