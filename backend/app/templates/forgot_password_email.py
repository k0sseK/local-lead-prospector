def get_forgot_password_email_html(reset_link: str) -> str:
    from datetime import datetime
    current_year = datetime.now().year
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset hasła - znajdzfirmy.pl</title>
    <style>
        @media only screen and (max-width: 620px) {{
            .container {{
                width: 100% !important;
                padding: 20px !important;
            }}
            .content {{
                padding: 30px 20px !important;
            }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0a0f0e; color: #ffffff;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0a0f0e;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table class="container" border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #111a18; border: 1px solid rgba(17, 153, 142, 0.2); border-radius: 24px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.5);">
                    <!-- Header with Logo/Name -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 10px 40px;">
                            <div style="font-size: 24px; font-weight: 600; letter-spacing: -0.5px; color: #38ef7d; text-decoration: none;">
                                <span style="color: #ffffff;">znajdz</span><span style="color: #38ef7d;">firmy&#8203;.&#8203;pl</span>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Main Body -->
                    <tr>
                        <td class="content" style="padding: 40px 50px 50px 50px;">
                            <h1 style="margin: 0 0 15px 0; font-size: 24px; font-weight: 700; color: #ffffff; text-align: center;">Zapomniałeś hasła?</h1>
                            <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.6; color: #94a3b8; text-align: center;">
                                Spokojnie, to się zdarza najlepszym. Kliknij przycisk poniżej, aby ustawić nowe hasło do swojego konta.
                            </p>
                            
                            <!-- Action Button -->
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td align="center" style="padding: 10px 0 30px 0;">
                                        <a href="{reset_link}" style="display: inline-block; padding: 16px 36px; font-size: 16px; font-weight: 700; color: #0a0f0e; text-decoration: none; background: linear-gradient(to right, #38ef7d, #11998e); background-color: #38ef7d; border-radius: 50px; box-shadow: 0 4px 15px rgba(56, 239, 125, 0.3);">
                                            Zresetuj hasło
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <div style="padding-top: 30px; border-top: 1px solid rgba(148, 163, 184, 0.1);">
                                <p style="margin: 0 0 10px 0; font-size: 14px; line-height: 1.5; color: #64748b; text-align: center;">
                                    Link wygaśnie za 15 minut ze względów bezpieczeństwa.<br>
                                    Jeśli to nie Ty prosiłeś o reset, zignoruj tę wiadomość.<br>
                                </p>
                            </div>
                            
                            <!-- Fallback Link -->
                            <p style="margin: 20px 0 0 0; font-size: 12px; line-height: 1.5; color: #475569; text-align: center;">
                                Przycisk nie działa? Wklej to w przeglądarce:<br>
                                <a href="{reset_link}" style="color: #11998e; text-decoration: none; word-break: break-all;">{reset_link}</a>
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: rgba(0, 0, 0, 0.2); text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #475569;">
                                &copy; {current_year} znajdzfirmy&#8203;.&#8203;pl
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
