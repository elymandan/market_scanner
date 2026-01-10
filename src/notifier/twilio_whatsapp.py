# Twilio WhatsApp notifier
from twilio.rest import Client
from .. import config

def send_whatsapp(text: str) -> bool:
    if not config.TWILIO_ACCOUNT_SID or not config.TWILIO_AUTH_TOKEN:
        return False
    client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
    try:
        msg = client.messages.create(
            body=text,
            from_=config.TWILIO_WHATSAPP_FROM,
            to=config.TWILIO_WHATSAPP_TO
        )
        return True
    except Exception as e:
        print("Twilio error:", e)
        return False