# Verklarende woordenlijst
___

- _service_name_: De naam van de service. Dit is een backend concept en correspondeerd met de folder namen in de root van de backend
- _module_slug_: De naam van de module als gezien vanuit de frontend. Dit kan overeen komen met de service_name, maar dat hoeft niet.
- _device_id_: Dit is de unieke ID die iOS en Android toestellen hebben. Deze ID wordt gebruikt om te bepalen welk toestel welke notificatie moet ontvangen. De ID veranderd niet voor eenzelfde toestel. Dit is eigenlijk altijd de hash van het daadwerkelijk device id van een toestel i.v.m. privacy.

#### Notifications
- _notification_: Een algemeen bericht onder het notificatie icoon in de app
- _push_notification_: Een bericht dat naar een toestel wordt gestuurd, ook wel een pushbericht genoemd. Voor elke push_notification bestaat er een record van een notification, maar dat geldt niet andersom.
- _notification_type_: binnen een frontend module kunnen meerdere types notificaties bestaan. Bijvoorbeeld een notificatie voor een aflopende parkeersessie en een notificatie voor een laag parkeersaldo. Voor deze types kan de push notificatie individueel aan en uitgezet worden.
