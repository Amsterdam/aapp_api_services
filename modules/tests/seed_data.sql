INSERT INTO modules_module (id,slug,status,app_reason,fallback_url,note,button_label) VALUES
	 (1,'about',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (2,'contact',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (3,'redirects',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (6,'report-problem',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (10,'onboarding',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (12,'construction-work',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (59,'burning-guide',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (11,'construction-work-editor',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (17,'city-pass',0,'Niet beschikbaar op de ontwikkel omgeving',NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (60,'open-city',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl');
INSERT INTO modules_module (id,slug,status,app_reason,fallback_url,note,button_label) VALUES
	 (62,'sport',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (63,'kingsday',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (64,'boat-charging',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (4,'welcome',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (51,'waste-container',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (9,'parking',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (65,'news',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (61,'service',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (50,'notification-history',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (41,'chat',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl');
INSERT INTO modules_module (id,slug,status,app_reason,fallback_url,note,button_label) VALUES
	 (52,'service-maps',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (53,'mijn-amsterdam',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (55,'elections',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (7,'waste-guide',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (58,'survey',1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl');

INSERT INTO modules_moduleversion (id,"version",title,icon,description,created,modified,module_id) VALUES
	 (1,'1.0.0','Afvalwijzer','trash-bin','Bekijk waar afval naartoe kan en wat de ophaaldagen zijn','2024-02-05 10:39:10.426945+01','2024-09-23 14:48:44.821702+02',7),
	 (3,'1.0.0','Werkzaamheden','construction-work','Blijf op de hoogte van werkzaamheden in uw buurt.','2024-02-05 10:39:10.442367+01','2024-02-28 16:43:08.953812+01',12),
	 (4,'1.0.0','Contact','chatting','Heeft u een vraag of wilt u iets weten?','2024-02-05 10:39:10.393362+01','2024-02-05 10:39:10.39337+01',2),
	 (5,'1.0.0','Melding doen','alert','Ziet u iets wat stuk is of opgeruimd moet worden?','2024-02-05 10:39:10.383926+01','2024-02-05 10:39:10.383942+01',6),
	 (7,'1.0.0','Over deze app','info','Lees meer over deze app en help ons de app verbeteren.','2024-02-05 10:39:10.41944+01','2024-02-05 10:39:10.419449+01',1),
	 (8,'1.0.0','Veel gezocht','eye','Op de website vindt u alle informatie die nog niet in de app zit.','2024-02-05 10:39:10.400925+01','2024-03-07 09:41:15.02341+01',3),
	 (9,'1.0.0','Plaats berichten','announcement','Hier kun je als omgevingsmanager berichten plaatsen bij werkzaamheden','2024-02-05 10:39:10.373698+01','2024-02-05 10:39:10.37371+01',11),
	 (11,'1.0.0','Welkomstscherm','info','Bekijk een mooi Amsterdams beeld bij het starten van de app','2024-02-05 10:39:10.457608+01','2026-06-10 14:17:01.374229+02',4),
	 (12,'1.0.1','Welkomstscherm','info','Bekijk een mooi Amsterdams beeld bij het starten van de app','2024-02-05 10:39:10.450569+01','2026-06-10 14:17:01.372885+02',4),
	 (32,'1.0.0','Stadspas','city-pass','Uw Stadspas gegevens en inzicht in uw saldo.','2024-07-08 13:37:59.627669+02','2024-07-25 11:57:39.636369+02',17);
INSERT INTO modules_moduleversion (id,"version",title,icon,description,created,modified,module_id) VALUES
	 (35,'1.0.2','Welkomstscherm','info','Bekijk een mooi Amsterdams beeld bij het starten van de app','2025-01-20 17:17:38.843081+01','2026-06-10 14:17:01.371319+02',4),
	 (37,'1.0.0','Onboarding','info','Onboarding van app','2024-02-05 10:39:10.483247+01','2024-02-05 10:39:10.483256+01',10),
	 (52,'1.0.0','Chat','chat','Salesforce chat','2024-09-16 16:49:54.028427+02','2024-09-16 20:32:00.100475+02',41),
	 (64,'1.0.0','Notificatiegeschiedenis','alert','Notificatiegeschiedenis','2024-11-21 16:35:40.420588+01','2024-11-21 16:35:40.420615+01',50),
	 (65,'1.0.0','Gfe/t container openen','trash-bin','Open een container met de app in plaats van een plastic pas.','2025-01-15 15:42:19.293649+01','2026-06-10 14:17:10.536093+02',51),
	 (66,'1.0.0','Aanmelden Parkeren','parking','Start en stop je parkeersessie','2025-02-20 14:05:20.144805+01','2025-02-24 09:26:06.109728+01',9),
	 (67,'1.0.0','Voorzieningenkaart','eye','Voorzieningenkaart','2025-03-25 10:11:35.866551+01','2025-03-25 10:11:35.866576+01',52),
	 (68,'1.0.0','Mijn Amsterdam','info','Ontvang pushberichten van Mijn Amsterdam','2025-07-31 14:16:50.729017+02','2025-07-31 14:16:50.729033+02',53),
	 (70,'1.0.0','Stembureaus','vote','Vind makkelijk een stembureau bij u in de buurt','2025-09-25 15:59:22.251314+02','2025-09-25 15:59:22.25133+02',55),
	 (71,'2.0.0','Afvalwijzer','trash-bag','Bekijk waar afval naartoe kan en wat de ophaaldagen zijn','2025-10-20 17:17:56.75583+02','2025-10-20 17:17:56.755847+02',7);
INSERT INTO modules_moduleversion (id,"version",title,icon,description,created,modified,module_id) VALUES
	 (74,'1.0.0','Klanttevredenheidsonderzoek','info','Klanttevredenheidsonderzoek','2025-11-20 12:00:15.977446+01','2025-11-20 12:00:15.977462+01',58),
	 (75,'1.0.0','Stookwijzer','fire','Weet wanneer u beter niet kunt stoken.','2025-11-25 16:03:15.287987+01','2025-11-26 12:56:03.987855+01',59),
	 (77,'1.0.0','Buurt idee','vote','Participeer in- en stem voor projecten in uw stadsdeel.','2026-02-03 10:56:25.156775+01','2026-02-03 10:56:25.156786+01',60),
	 (79,'1.0.0','Handig in de stad','alert','Bekijk kaarten met verschillende voorzieningen in de stad.','2026-03-04 10:53:05.487527+01','2026-06-15 10:45:10.550738+02',61),
	 (80,'1.0.1','Handig in de stad','map-marker-on-map','Bekijk kaarten met verschillende voorzieningen in de stad.','2026-03-04 12:24:59.751369+01','2026-06-15 10:45:10.546107+02',61),
	 (81,'1.0.0','Sport','fire','Krijg inzicht in sportvoorzieningen in de stad en beheer sportgerelateerde reserveringen en boekingen.','2026-03-31 10:45:06.169042+02','2026-03-31 10:45:06.169053+02',62),
	 (82,'1.0.0','Koningsdag','crown','Bekijk praktische informatie voor Koningsdag.','2026-04-13 16:45:28.23704+02','2026-04-14 11:02:30.916008+02',63),
	 (83,'1.0.0','Boot laden','boat-charging','Laad uw elektrische boot op.','2026-05-04 17:30:42.286426+02','2026-05-04 17:30:42.286437+02',64),
	 (84,'1.0.0','Nieuws','newspaper','Blijf op de hoogte van nieuws uit de stad en uw stadsdeel.','2026-05-20 10:40:30.479911+02','2026-06-10 15:02:32.955622+02',65);


INSERT INTO modules_apprelease (id,"version",release_notes,published,unpublished,created,modified,deprecated,module_order) VALUES
	 (63,'1.26.0','',NULL,NULL,'2026-03-19 15:10:21.754361+01','2026-04-22 13:27:26.459183+02',NULL,NULL),
	 (64,'1.27.0','',NULL,NULL,'2026-04-22 13:30:31.606044+02','2026-05-20 11:14:41.601563+02',NULL,NULL),
	 (65,'1.28.0','',NULL,NULL,'2026-06-15 14:56:26.334775+02','2026-06-15 15:01:59.097724+02',NULL,NULL);


INSERT INTO modules_releasemodulestatus (id,status,app_release_id,module_version_id,sort_order,app_reason,fallback_url,note,button_label) VALUES
	 (1379,1,65,82,1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1380,1,65,9,2,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1381,1,65,68,3,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1382,1,65,66,4,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1383,1,65,37,5,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1384,1,65,71,6,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1336,1,63,9,1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1337,1,63,68,3,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1338,1,63,66,4,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1339,1,63,37,5,NULL,NULL,NULL,'Bekijk op Amsterdam.nl');
INSERT INTO modules_releasemodulestatus (id,status,app_release_id,module_version_id,sort_order,app_reason,fallback_url,note,button_label) VALUES
	 (1340,1,63,71,6,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1385,1,65,70,7,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1386,1,65,84,8,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1387,1,65,3,9,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1388,1,65,5,10,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1389,1,65,65,11,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1390,1,65,32,12,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1391,1,65,83,14,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1392,1,65,75,15,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1393,1,65,4,16,NULL,NULL,NULL,'Bekijk op Amsterdam.nl');
INSERT INTO modules_releasemodulestatus (id,status,app_release_id,module_version_id,sort_order,app_reason,fallback_url,note,button_label) VALUES
	 (1394,1,65,8,17,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1395,1,65,7,18,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1396,1,65,64,19,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1397,1,65,52,20,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1398,1,65,74,21,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1348,1,63,8,16,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1349,1,63,7,17,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1350,1,63,64,18,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1351,1,63,52,19,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1352,1,63,74,20,NULL,NULL,NULL,'Bekijk op Amsterdam.nl');
INSERT INTO modules_releasemodulestatus (id,status,app_release_id,module_version_id,sort_order,app_reason,fallback_url,note,button_label) VALUES
	 (1376,1,64,83,14,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1399,1,65,80,13,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1356,1,63,82,2,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1377,1,64,82,1,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1341,1,63,70,7,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1342,1,63,3,9,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1343,1,63,5,11,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1346,1,63,75,14,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1347,1,63,4,15,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1378,1,64,84,9,NULL,NULL,NULL,'Bekijk op Amsterdam.nl');
INSERT INTO modules_releasemodulestatus (id,status,app_release_id,module_version_id,sort_order,app_reason,fallback_url,note,button_label) VALUES
	 (1354,1,63,80,8,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1357,1,64,9,2,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1359,1,64,68,3,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1360,1,64,66,4,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1361,1,64,37,5,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1362,1,64,71,6,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1363,1,64,70,7,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1364,1,64,3,10,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1365,1,64,5,11,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1366,1,64,65,12,NULL,NULL,NULL,'Bekijk op Amsterdam.nl');
INSERT INTO modules_releasemodulestatus (id,status,app_release_id,module_version_id,sort_order,app_reason,fallback_url,note,button_label) VALUES
	 (1367,1,64,32,13,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1368,1,64,75,15,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1344,1,63,65,12,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1345,1,63,32,13,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1375,1,64,80,8,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1369,1,64,4,16,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1370,1,64,8,17,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1371,1,64,7,18,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1372,1,64,64,19,NULL,NULL,NULL,'Bekijk op Amsterdam.nl'),
	 (1373,1,64,52,20,NULL,NULL,NULL,'Bekijk op Amsterdam.nl');
INSERT INTO modules_releasemodulestatus (id,status,app_release_id,module_version_id,sort_order,app_reason,fallback_url,note,button_label) VALUES
	 (1374,1,64,74,21,NULL,NULL,NULL,'Bekijk op Amsterdam.nl');
