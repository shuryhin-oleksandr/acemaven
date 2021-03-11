import json

import requests
from rest_framework import serializers

result = [
    {'status': 'ATIVA', 'calendario': {'criacao': '2021-02-05T05:32:59.91-03:00', 'expiracao': '86400'},
     'location': 'qrcodepix-h.bb.com.br/pix/v2/34b93368-aeb0-4b90-bd8f-4f5fbfc7af76',
     'textoImagemQRcode': '00020101021226870014br.gov.bcb.pix2565qrcodepix-h.bb.com.br/pix/v2/34b93368-aeb0-4b90-bd8f-4f5fbfc7af765204000053039865406501.005802BR5920ALAN GUIACHERO BUENO6008BRASILIA62070503***6304E4EE',
     'txid': '6fwbeg8tlbrozfc62iizlstdg0y41be1tfe', 'revisao': 0,
     'devedor': {'cpf': '12345678909', 'nome': 'Francisco da Silva'}, 'valor': {'original': '501.0'},
     'chave': 'testqrcode01@bb.com.br', 'solicitacaoPagador': 'Cobrança dos serviços prestados.'},
    {'status': 'ATIVA', 'calendario': {'criacao': '2021-02-05T05:33:03.62-03:00', 'expiracao': '86400'},
     'location': 'qrcodepix-h.bb.com.br/pix/v2/98fba25b-d284-4478-8079-a9be32eaab67',
     'textoImagemQRcode': '00020101021226870014br.gov.bcb.pix2565qrcodepix-h.bb.com.br/pix/v2/98fba25b-d284-4478-8079-a9be32eaab675204000053039865406502.005802BR5920ALAN GUIACHERO BUENO6008BRASILIA62070503***6304FE6C',
     'txid': '2a1hhwt0s3x0307kuxme6zwp2i2cpyn9bn2', 'revisao': 0,
     'devedor': {'cpf': '12345678909', 'nome': 'Francisco da Silva'}, 'valor': {'original': '502.0'},
     'chave': 'testqrcode01@bb.com.br', 'solicitacaoPagador': 'Cobrança dos serviços prestados.'},
    {'status': 'ATIVA', 'calendario': {'criacao': '2021-02-05T05:33:06.72-03:00', 'expiracao': '86400'},
     'location': 'qrcodepix-h.bb.com.br/pix/v2/e4bc34aa-2720-45b6-a687-22c161a271e8',
     'textoImagemQRcode': '00020101021226870014br.gov.bcb.pix2565qrcodepix-h.bb.com.br/pix/v2/e4bc34aa-2720-45b6-a687-22c161a271e85204000053039865406503.005802BR5920ALAN GUIACHERO BUENO6008BRASILIA62070503***63047DFC',
     'txid': 'yp6j3rvyq0455qawd6vy1sybuzb2w4394ov', 'revisao': 0,
     'devedor': {'cpf': '12345678909', 'nome': 'Francisco da Silva'}, 'valor': {'original': '503.0'},
     'chave': 'testqrcode01@bb.com.br', 'solicitacaoPagador': 'Cobrança dos serviços prestados.'},
    {'status': 'ATIVA', 'calendario': {'criacao': '2021-02-05T05:33:09.85-03:00', 'expiracao': '86400'},
     'location': 'qrcodepix-h.bb.com.br/pix/v2/80701261-8647-4890-ac28-58fba4e7f449',
     'textoImagemQRcode': '00020101021226870014br.gov.bcb.pix2565qrcodepix-h.bb.com.br/pix/v2/80701261-8647-4890-ac28-58fba4e7f4495204000053039865406504.005802BR5920ALAN GUIACHERO BUENO6008BRASILIA62070503***63045EBD',
     'txid': '4qxjxskjx4vqcehrobswvgmojcxg59smyuz', 'revisao': 0,
     'devedor': {'cpf': '12345678909', 'nome': 'Francisco da Silva'}, 'valor': {'original': '504.0'},
     'chave': 'testqrcode01@bb.com.br', 'solicitacaoPagador': 'Cobrança dos serviços prestados.'},
    {'status': 'ATIVA', 'calendario': {'criacao': '2021-02-05T05:33:13.11-03:00', 'expiracao': '86400'},
     'location': 'qrcodepix-h.bb.com.br/pix/v2/370fa0ef-2ea7-4769-8b63-92e277a323a1',
     'textoImagemQRcode': '00020101021226870014br.gov.bcb.pix2565qrcodepix-h.bb.com.br/pix/v2/370fa0ef-2ea7-4769-8b63-92e277a323a15204000053039865406505.005802BR5920ALAN GUIACHERO BUENO6008BRASILIA62070503***63048636',
     'txid': 'btma0oj36q3ohavpai9mnxcqwlg86rv1z9g', 'revisao': 0,
     'devedor': {'cpf': '12345678909', 'nome': 'Francisco da Silva'}, 'valor': {'original': '505.0'},
     'chave': 'testqrcode01@bb.com.br', 'solicitacaoPagador': 'Cobrança dos serviços prestados.'},
    {'status': 'ATIVA', 'calendario': {'criacao': '2021-02-05T05:33:16.24-03:00', 'expiracao': '86400'},
     'location': 'qrcodepix-h.bb.com.br/pix/v2/e3d9c9bb-32c6-428a-842b-96c0d71210de',
     'textoImagemQRcode': '00020101021226870014br.gov.bcb.pix2565qrcodepix-h.bb.com.br/pix/v2/e3d9c9bb-32c6-428a-842b-96c0d71210de5204000053039865406506.005802BR5920ALAN GUIACHERO BUENO6008BRASILIA62070503***63041E96',
     'txid': '8kbtlb89vw75uqus8mxftwj8sxud65704ew', 'revisao': 0,
     'devedor': {'cpf': '12345678909', 'nome': 'Francisco da Silva'}, 'valor': {'original': '506.0'},
     'chave': 'testqrcode01@bb.com.br', 'solicitacaoPagador': 'Cobrança dos serviços prestados.'},

    {'status': 'ATIVA', 'calendario': {'criacao': '2021-02-05T05:33:19.44-03:00', 'expiracao': '86400'},
     'location': 'qrcodepix-h.bb.com.br/pix/v2/2bb044e4-f856-4be1-af33-258a9f452992',
     'textoImagemQRcode': '00020101021226870014br.gov.bcb.pix2565qrcodepix-h.bb.com.br/pix/v2/2bb044e4-f856-4be1-af33-258a9f4529925204000053039865406507.005802BR5920ALAN GUIACHERO BUENO6008BRASILIA62070503***6304ED5F',
     'txid': 'mf7f9xuh4uirosql80dd7qzh989loex9sif', 'revisao': 0,
     'devedor': {'cpf': '12345678909', 'nome': 'Francisco da Silva'}, 'valor': {'original': '507.0'},
     'chave': 'testqrcode01@bb.com.br', 'solicitacaoPagador': 'Cobrança dos serviços prestados.'},
    {'status': 'ATIVA', 'calendario': {'criacao': '2021-02-05T05:33:23.04-03:00', 'expiracao': '86400'},
     'location': 'qrcodepix-h.bb.com.br/pix/v2/13f16717-aeea-4c08-bc89-94879b83c06d',
     'textoImagemQRcode': '00020101021226870014br.gov.bcb.pix2565qrcodepix-h.bb.com.br/pix/v2/13f16717-aeea-4c08-bc89-94879b83c06d5204000053039865406508.005802BR5920ALAN GUIACHERO BUENO6008BRASILIA62070503***6304903C',
     'txid': '56dzpsv1cevwawuu3p061qe2n6nqat64s6q', 'revisao': 0,
     'devedor': {'cpf': '12345678909', 'nome': 'Francisco da Silva'}, 'valor': {'original': '508.0'},
     'chave': 'testqrcode01@bb.com.br', 'solicitacaoPagador': 'Cobrança dos serviços prestados.'},
    {'status': 'ATIVA', 'calendario': {'criacao': '2021-02-05T05:33:25.93-03:00', 'expiracao': '86400'},
     'location': 'qrcodepix-h.bb.com.br/pix/v2/565365b1-02e1-4dfe-b378-bfff6a8aba17',
     'textoImagemQRcode': '00020101021226870014br.gov.bcb.pix2565qrcodepix-h.bb.com.br/pix/v2/565365b1-02e1-4dfe-b378-bfff6a8aba175204000053039865406509.005802BR5920ALAN GUIACHERO BUENO6008BRASILIA62070503***6304D3A3',
     'txid': '4kspj9um8yspmfwyoh0ftga5h82glz5f381', 'revisao': 0,
     'devedor': {'cpf': '12345678909', 'nome': 'Francisco da Silva'}, 'valor': {'original': '509.0'},
     'chave': 'testqrcode01@bb.com.br', 'solicitacaoPagador': 'Cobrança dos serviços prestados.'},
    {'status': 'ATIVA', 'calendario': {'criacao': '2021-02-05T05:33:29.49-03:00', 'expiracao': '86400'},
     'location': 'qrcodepix-h.bb.com.br/pix/v2/36657b89-bbab-4253-a6de-cf86e35d7647',
     'textoImagemQRcode': '00020101021226870014br.gov.bcb.pix2565qrcodepix-h.bb.com.br/pix/v2/36657b89-bbab-4253-a6de-cf86e35d76475204000053039865406510.005802BR5920ALAN GUIACHERO BUENO6008BRASILIA62070503***6304CF52',
     'txid': 'p1y3advrdeb5awnqb8sby2xav6cjy4sjqdw', 'revisao': 0,
     'devedor': {'cpf': '12345678909', 'nome': 'Francisco da Silva'}, 'valor': {'original': '510.0'},
     'chave': 'testqrcode01@bb.com.br', 'solicitacaoPagador': 'Cobrança dos serviços prestados.'},
]


def get_credentials(token_uri, client_id, client_secret, basic_token):
    response = requests.post(
        f'{token_uri}',
        headers={
            'content-type': 'application/x-www-form-urlencoded',
            'authorization': f'Basic {basic_token}',
        },
        data={
            'grant_type': 'client_credentials',
            'client_id': f'{client_id}',
            'client_secret': f'{client_secret}',
            'scope': 'cob.write cob.read pix.read pix.write',
        }
    )

    if response.status_code == 200:
        response_json = response.json()
        return response_json.get('access_token')


def get_qr_code(amount, txid, pix_key, qr_cob_uri, developer_key, token_uri, client_id, client_secret,
                basic_token, is_prod=False):
    token = get_credentials(token_uri, client_id, client_secret, basic_token)
    response = requests.put(
        f'{qr_cob_uri}{txid}?gw{"-dev" if not is_prod else ""}-app-key={developer_key}',
        data=json.dumps({
            "calendario": {
                "criacao": "2021-2-1T13:09:39.9200140000",
                "expiracao": "259200"
            },
            "txid": f"{txid}",
            "devedor": {
                "cpf": "12345678909",
                "nome": "Francisco da Silva"
            },
            "valor": {
                "original": f"{amount}"
            },
            "chave": f"{pix_key}",
            "solicitacaoPagador": "Cobrança dos serviços prestados."
        }),
        headers={
            'content-type': 'application/json',
            'authorization': f'Bearer {token}'}
    )
    if qr_code := response.json().get('textoImagemQRcode'):
        return qr_code
    else:
        raise serializers.ValidationError({'error': 'Some issues occurred during payment process, please contact support or retry.'})


def change_amount(base_url, new_amount, developer_key, txid, is_prod, token_uri, client_id, client_secret, basic_token):
    token = get_credentials(token_uri, client_id, client_secret, basic_token)
    response = requests.patch(
        f'{base_url}{txid}?gw{"-dev" if not is_prod else ""}-app-key={developer_key}',
        data=json.dumps({
            "valor": {
                "original": f"{new_amount}"
            }}),
        headers={
            'content-type': 'application/json',
            'authorization': f'Bearer {token}'}
    )
    try:
        data = response.json()
    except ValueError:
        data = "Invalid json"
    return data, response.status_code


def review_payment(base_url, developer_key, txid, token_uri, client_id, client_secret, basic_token, is_prod=False):
    token = get_credentials(token_uri, client_id, client_secret, basic_token)
    response = requests.get(
        f'{base_url}{txid}?gw{"-dev" if not is_prod else ""}-app-key={developer_key}',
        headers={
            'content-type': 'application/json',
            'authorization': f'Bearer {token}'}
    )
    try:
        data = response.json()
    except ValueError:
        data = "Invalid json"
    return data, response.status_code
