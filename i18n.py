"""Arabic, English, French and Kinyarwanda interface labels."""
from __future__ import annotations
STRINGS={
"dashboard":{"ar":"لوحة التحكم","en":"Dashboard","fr":"Tableau de bord","rw":"Ikibaho"},
"vision":{"ar":"الرؤية والكاميرا","en":"Vision","fr":"Vision","rw":"Icyerekezo"},
"translation":{"ar":"الترجمة","en":"Translation","fr":"Traduction","rw":"Ubuhinduzi"},
"meetings":{"ar":"الاجتماعات","en":"Meetings","fr":"Réunions","rw":"Inama"},
"ask_ai":{"ar":"اسأل الذكاء الاصطناعي","en":"Ask AI","fr":"Demander à l’IA","rw":"Baza AI"},
"security":{"ar":"الأمان","en":"Security","fr":"Sécurité","rw":"Umutekano"},
"data_control":{"ar":"إدارة البيانات","en":"Data Control","fr":"Contrôle des données","rw":"Kugenzura amakuru"},
"settings":{"ar":"الإعدادات","en":"Settings","fr":"Paramètres","rw":"Igenamiterere"},
"logout":{"ar":"تسجيل الخروج","en":"Logout","fr":"Déconnexion","rw":"Sohoka"},
"refresh":{"ar":"تحديث","en":"Refresh","fr":"Actualiser","rw":"Ongera"},
"ready":{"ar":"النظام جاهز","en":"System ready","fr":"Système prêt","rw":"Sisitemu iriteguye"},
}
def tr(key: str,language: str="en")->str: return STRINGS.get(key,{}).get(language,STRINGS.get(key,{}).get('en',key))
