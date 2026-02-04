import logging

from rest_framework import generics, status
from rest_framework.response import Response

from contact.exceptions import LinkDataException
from contact.serializers.links_serializers import LinksOutSerializer

logger = logging.getLogger(__name__)


class LinksView(generics.RetrieveAPIView):
    serializer_class = LinksOutSerializer
    links = {
        "acknowledgeChild": "https://www.amsterdam.nl/veelgevraagd/een-kind-erkennen-b0bd7",
        "birth": "https://www.amsterdam.nl/burgerzaken/geboorte-erkenning-kinderen/geboorteaangifte/",
        "chatPrivacy": "https://www.amsterdam.nl/privacy/specifieke/privacyverklaringen-burgerzaken-contact/klantcontact/",
        "citypass": "https://www.amsterdam.nl/stadspas/",
        "contactForm": "https://formulieren.amsterdam.nl/TriplEforms/DirectRegelen/formulier/nl-NL/evAmsterdam/Contactformulier.aspx",
        "cityPassRequest": "https://formulieren.amsterdam.nl/TriplEforms/DirectRegelen/formulier/nl-NL/evAmsterdam/HulpBijLaagInkomen.aspx",
        "cityPassChildBudget": "https://www.amsterdam.nl/stadspas/kindtegoed/",
        "cityPassUsage": "https://www.amsterdam.nl/stadspas/werkt-stadspas/",
        "cityPassLowIncomeSupport": "https://www.amsterdam.nl/werk-en-inkomen/regelingen-bij-laag-inkomen-pak-je-kans/",
        "contactNewsletterSignup": "https://cloud.nieuwsbrief.amsterdam.nl/nieuwsbrief-aanmelden?type=amsterdam",
        "documents": "https://www.amsterdam.nl/burgerzaken/akten-uittreksels/",
        "elections": "https://www.amsterdam.nl/verkiezingen/",
        "feedbackForm": "https://formulier.amsterdam.nl/thema/burgerzaken/amsterdam-app/Uw-mening/",
        "immigration": "https://www.amsterdam.nl/burgerzaken/immigratie",
        "income_help": "https://www.amsterdam.nl/werk-inkomen/hulp-bij-laag-inkomen/",
        "lifelessBirth": "https://www.amsterdam.nl/veelgevraagd/levenloos-geboren-kindje-registreren-in-de-brp-daaf8#case_%7BB104B52F-9A3B-4923-8B5D-1FA60B6F3591%7D",
        "makeAppointMentWeesp": "https://formulieren.amsterdam.nl/TriplEforms/DirectRegelen/formulier/nl-NL/evAmsterdam/afspraakmakenweesp.aspx",
        "marriage": "https://www.amsterdam.nl/burgerzaken/trouwen-en-partnerschap/",
        "marriagePermission": "https://www.amsterdam.nl/veelgevraagd/verklaring-van-huwelijksbevoegdheid-9fedd#case_%7B0F588CAC-30A3-4ED1-B355-10F9EE8759D9%7D",
        "my_parking": "https://parkeervergunningen.amsterdam.nl/",
        "my_reported_problems": "https://meldingen.amsterdam.nl/mijn-meldingen/login",
        "naturalisation": "https://www.amsterdam.nl/burgerzaken/naturalisatie",
        "parking": "https://www.amsterdam.nl/parkeren/",
        "parking_request_license_plate_ga_bewoners": "https://www.amsterdam.nl/parkeren/parkeren-gehandicapten/parkeervergunning-gehandicapte-bewoners/gehandicapte-bewoners-kenteken-wijzigen/",
        "parking_request_license_plate_ga_bezoekers": "https://www.amsterdam.nl/parkeren/parkeren-gehandicapten/parkeervergunning-gehandicapte-bezoekers/gehandicapte-bezoekers-kenteken-wijzigen/",
        "parking_request_license_plate_mantelzorgers": "https://www.amsterdam.nl/parkeren/parkeervergunning/parkeervergunning-voor-mantelzorgers/parkeervergunning-mantelzorgers-kenteken/",
        "passing": "https://www.amsterdam.nl/burgerzaken/overlijden/aangifte-overlijden/",
        "passingForFuneralDirectors": "https://www.amsterdam.nl/burgerzaken/overlijden/aangifte-overlijden-uitvaartondernemers/",
        "reported_problems_map": "https://meldingen.amsterdam.nl/meldingenkaart",
        "relocation": "https://www.amsterdam.nl/burgerzaken/verhuizing-doorgeven/",
        "rivm_report": "https://www.atlasleefomgeving.nl/stookwijzer",
        "sailingAndMooring": "https://www.amsterdam.nl/verkeer-vervoer/varen/vaarvignet-aanvragen/",
        "waste": "https://www.amsterdam.nl/afval/",
        "waste_extra_info": "https://www.milieucentraal.nl/",
    }

    def get(self, request, *args, **kwargs):
        output_serializer = self.get_serializer(data=self.links)
        if not output_serializer.is_valid():
            logger.error(
                f"Link data not in expected format: {output_serializer.errors}"
            )
            raise LinkDataException()

        return Response(output_serializer.data, status=status.HTTP_200_OK)
