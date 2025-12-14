import json
import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def generate_sslcommerz_payment(request, order):
    post_body = {
        'store_id': settings.SSLCOMMERZE_STORE_ID,
        'store_passwd': settings.SSLCOMMERZE_STORE_PASSWORD,
        'total_amount': float(order.get_total_cost()),
        'currency': 'BDT',
        'tran_id': str(order.id),
        'success_url': request.build_absolute_uri(f'/payment/success/{order.id}/'),
        'fail_url': request.build_absolute_uri(f'/payment/fail/{order.id}/'),
        'cancel_url': request.build_absolute_uri(f'/payment/cancel/{order.id}/'),
        'cus_name': f'{order.first_name} {order.last_name}',
        'cus_email': order.email,
    }

    response = requests.post(
        settings.SSLCOMMERZE_PAYMENT_URL,
        data=post_body
    )

    return response.json()
