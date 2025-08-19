# Messenger - Discord Bridge Bot (Replit + UptimeRobot)

Ez a bot összeköt egy *Messenger csoportot* és egy *Discord csatornát*:
   - *Messenger*-ből *Discord*-ba: minden üzenet + fájl átmegy, a videók automatikusan 3GP formátumra konvertálódnak (ffmpeg).
   - *Discord*-ból *Messenger*-be: minden üzenet + fájl változatlanul átmegy.
   - A *Messenger*-ből *Discord*-ba üzenetek *Webhook*-on keresztül mennek, tehát úgy néznek ki, mintha a felhasználó maga írta volna (mint TupperBox).
   - A bot *Replit*-en fut, az *UptimeRobot* pedig ébren tartja *24/7*-ben.

# Telepítési folyamat:

# 1. Discord Bot létrehozása
1. Menj a [Discord Developer Portal](https://discord.com/developers/applications) oldalra.
2. Kattints *New Application* - adj neki nevet (pl. `MessengerBridgeBot`).
3. Bal oldalt menj a *Bot* fülre, majd kattints *Add Bot*.
4. Másold ki a *TOKEN*-t - ezt majd a Replit Secrets-ben `DISCORD_TOKEN` néven kell megadni.
5. A bot engedélyeihez kapcsold be:
   - *MESSAGE CONTENT INTENT*
   - *SERVER MEMBERS INTENT*
6. Menj az *OAuth2/URL Generator* menübe:
   - Scopes: *bot*
   - Bot permissions: *Send Messages*, *Read Messages/View Channels*, *Attach Files*
   - Nyisd meg a generált linket és add hozzá a botot a szerveredhez.

# 2. Discord Webhook létrehozása
1. Discord - csatorna beállítások - *Integrations/Webhooks*.
2. Kattints *New Webhook*.
3. Adj neki tetszőleges nevet (pl. `Messenger Bridge Webhook`).
4. Másold ki az *URL*-t - ezt a Replit Secrets-ben `DISCORD_WEBHOOK_URL` néven kell megadni.
   ###### Megjegyzés: Ezzel érjük el, hogy a bot a Messenger felhasználók nevében küldjön üzeneteket, mintha tényleg ők írták volna.

# 3. Discord csatorna ID megszerzése
1. Discord - *User Settings/Advanced/Developer Mode* kapcsoló be.
2. Jobb klikk a kívánt csatornára - *Copy Channel ID*.
3. Ezt kell a Replit Secrets-ben `DISCORD_CHANNEL_ID` néven megadni.

# 4. Messenger adatok (COOKIE-s bejelentkezés)
A bot NEM email/jelszóval lép be, hanem a böngészőben tárolt Facebook cookie-kat használja.  
Ehhez két értéket kell kimásolni a böngésződből:

1. Nyisd meg a [Messenger](https://www.messenger.com/) oldalt, és lépj be a Facebook fiókoddal.
2. Nyomj *F12*-t a fejlesztői eszközök megnyitásához.
3. Menj az *Application (vagy Storage)* fülre - *Cookies* - `facebook.com`.
4. Másold ki ezek értékét:
   - `c_user`
   - `xs`

Ezeket kell majd Replit Secrets-ben beállítani:
- `FB_COOKIE_CUSER` = a `c_user` cookie értéke
- `FB_COOKIE_XS` = az `xs` cookie értéke

Messenger csoport ID:
1. Nyisd meg a csoport beszélgetést böngészőben.
2. Az URL így néz ki:
   ```
   https://www.facebook.com/messages/t/1234567890123456
   ```
3. A szám a végén = `MESSENGER_THREAD_ID`.

# 5. Replit Secrets beállítás
Replit-en *Tools/Secrets* menüben add hozzá az alábbiakat:

- `DISCORD_TOKEN` - A Discord bot *TOKEN*-je
- `DISCORD_CHANNEL_ID` - A cél Discord csatorna *ID*-ja
- `DISCORD_WEBHOOK_URL` - A Discord csatorna *Webhook URL*-je
- `FB_COOKIE_CUSER` - Messenger `c_user` cookie értéke
- `FB_COOKIE_XS` - Messenger `xs` cookie értéke
- `MESSENGER_THREAD_ID` - Messenger csoport *ID*-ja

# 6. UptimeRobot beállítása (24/7 működéshez)
1. Menj az [https://uptimerobot.com/](https://uptimerobot.com/) oldalra és hozz létre egy ingyenes accountot.
2. Hozz létre egy *HTTP(s) Monitor*-t:
   - *URL*:
     ```
     https://<a-te-repl-neved>.<felhasznalo>.repl.co/
     ```
   - *Interval*: 5 perc.
3. Ha pingeli a botot, az ébren marad.

# 7. Hibakeresés

- *Bot nem indul* - Ellenőrizd a `requirements.txt` és `replit.nix` fájlokat.
- *Messenger login hiba* - Ellenőrizd, hogy a `c_user` és `xs` cookie értékei helyesek-e, és nem jártak le.
- *Nem látja a csatornát* - Ellenőrizd a `DISCORD_CHANNEL_ID` értéket.
- *Webhook nem működik* - Nézd meg, hogy a `DISCORD_WEBHOOK_URL` titkos változó jó-e.
- *Videó konvertálás hiba* - Nézd a logot, ott az ffmpeg hibaüzenet.
