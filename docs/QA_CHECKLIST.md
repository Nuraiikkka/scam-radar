# QA checklist before the presentation (10 minutes)

Do it once on a phone (Android app or phone browser) and once in a laptop browser.
Tick each box. If something fails, write the step number in the team chat.

## Start

1. [ ] `https://your-domain/api/v1/health` shows `"status":"ok"`.
2. [ ] Open the app. The introduction shows three pages; "Skip" jumps to the last one.
3. [ ] "I understand, start" opens the Check screen. Reopen the app: no introduction.

## Check a video

4. [ ] Tap "Check link" with an empty field: "Paste a link first".
5. [ ] Type `https://youtube.com/x`: "This is not a TikTok link".
6. [ ] Paste a real public TikTok link and check it. Stages change, a result appears.
7. [ ] Upload `data/samples/scam_invest_ru.mp4`. Result: high risk, "Investment platform".
8. [ ] Open "Text on screen" and "QR codes" on the result. Evidence is there.
9. [ ] Tap "Share". The share sheet opens (phone) or "Result copied" shows (laptop).
10. [ ] "Wrong verdict?" → "No, it is wrong" → pick a category → Send. "Thank you!" shows.
11. [ ] Upload `data/samples/safe_cooking_ru.mp4`. Result: low risk, "No scam signs".
12. [ ] Phone only: share a TikTok link from the TikTok app to Scam Radar. The link is filled in.

## History and statistics

13. [ ] History shows both checks with colours and dates.
14. [ ] Search "cooking": only that item stays. Clear the search.
15. [ ] Tap the "Investment platform" chip, then "All".
16. [ ] Swipe one item to the left: it disappears and "Deleted" shows.
17. [ ] Pull down (or tap the refresh icon): the list reloads.
18. [ ] Statistics shows the number of checks and both charts. "Everyone" works.

## Settings and account

19. [ ] Switch to "Русский": the whole app is in Russian, results show Russian reasons.
20. [ ] Switch theme to Dark and back to Light.
21. [ ] "Log in or register" → "No account? Register" → create an account.
22. [ ] "Logged in as …" is shown. History is still there.
23. [ ] Log out, log in with a wrong password: "Wrong email or password." Then log in correctly.
24. [ ] "Clear history" → Cancel keeps items; Confirm deletes them.

## Failure cases

25. [ ] Turn on airplane mode: the red offline banner appears. Turn it off: it goes away.
26. [ ] Upload a photo or a PDF: a clear "file type is not supported" message.
27. [ ] Admin panel `https://your-domain/admin` opens with the admin account; feedback is listed.

## After the demo

28. [ ] Check `docker compose -f deploy/docker-compose.prod.yml ps`: all services healthy.
