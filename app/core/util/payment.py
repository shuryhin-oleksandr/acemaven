import json

import requests

from app.core.utils import get_random_string

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


def get_credentials():
    response = requests.post(
        'https://oauth.hm.bb.com.br/oauth/token',
        headers={
            'content-type': 'application/x-www-form-urlencoded',
            'authorization': 'Basic ZXlKcFpDSTZJamt3WW1NMVlUZ3RObUU0TXkwMFkyRXpMU0lzSW1OdlpHbG5iMUIxWW14cFkyRmtiM0lpT2pBc0ltTnZaR2xuYjFOdlpuUjNZWEpsSWpveE1qSTNNQ3dpYzJWeGRXVnVZMmxoYkVsdWMzUmhiR0ZqWVc4aU9qRjk6ZXlKcFpDSTZJakZoTURKaFptWXRNMkl6TnkwME5HSXpMV0V3T0RndFpUUTJNVEZoTmprMU9HWXlNRGN6Tm1JNE4yUXRObVU0SWl3aVkyOWthV2R2VUhWaWJHbGpZV1J2Y2lJNk1Dd2lZMjlrYVdkdlUyOW1kSGRoY21VaU9qRXlNamN3TENKelpYRjFaVzVqYVdGc1NXNXpkR0ZzWVdOaGJ5STZNU3dpYzJWeGRXVnVZMmxoYkVOeVpXUmxibU5wWVd3aU9qRXNJbUZ0WW1sbGJuUmxJam9pYUc5dGIyeHZaMkZqWVc4aUxDSnBZWFFpT2pFMk1EZzNOemczTVRrMU5UZDk=',
        },
        data={
            'grant_type': 'client_credentials',
            'client_id': 'eyJpZCI6IjkwYmM1YTgtNmE4My00Y2EzLSIsImNvZGlnb1B1YmxpY2Fkb3IiOjAsImNvZGlnb1NvZnR3YXJlIjoxMjI3MCwic2VxdWVuY2lhbEluc3RhbGFjYW8iOjF9',
            'client_secret': 'eyJpZCI6IjFhMDJhZmYtM2IzNy00NGIzLWEwODgtZTQ2MTFhNjk1OGYyMDczNmI4N2QtNmU4IiwiY29kaWdvUHVibGljYWRvciI6MCwiY29kaWdvU29mdHdhcmUiOjEyMjcwLCJzZXF1ZW5jaWFsSW5zdGFsYWNhbyI6MSwic2VxdWVuY2lhbENyZWRlbmNpYWwiOjEsImFtYmllbnRlIjoiaG9tb2xvZ2FjYW8iLCJpYXQiOjE2MDg3Nzg3MTk1NTd9',
            'scope': 'cob.write cob.read pix.read pix.write',
        }
    )

    if response.status_code == 200:
        response_json = response.json()
        return response_json.get('access_token')


def get_qr_code(amount, txid, token):
    response = requests.put(
        f'https://api.hm.bb.com.br/pix/v1/cobqrcode/{txid}?gw-dev-app-key=d27b377907ffab40136ee17da0050e56b941a5b4',
        data=json.dumps({
            "calendario": {
                "criacao": "2021-2-1T13:09:39.9200140000",
                "expiracao": "86400"
            },
            "txid": f"{txid}",
            "devedor": {
                "cpf": "12345678909",
                "nome": "Francisco da Silva"
            },
            "valor": {
                "original": f"{amount}"
            },
            "chave": "testqrcode01@bb.com.br",
            "solicitacaoPagador": "Cobrança dos serviços prestados."
        }),
        headers={
            'content-type': 'application/json',
            'authorization': f'Bearer {token}'}
    )
    if qr_code := response.json()['textoImagemQRcode']:
        return qr_code
    else:
        return 'Have some problems getting QR-code'


def change_amount(new_amount, token, txid):
    response = requests.patch(
        f'https://api.hm.bb.com.br/pix/v1/cob/{txid}?gw-dev-app-key=d27b377907ffab40136ee17da0050e56b941a5b4',
        data=json.dumps({
            "valor": {
                "original": f"{new_amount}"
            }}),
        headers={
            'content-type': 'application/json',
            'authorization': f'Bearer {token}'}
    )
    if response.status_code == 200:
        response_json = response.json()
        return response_json
    else:
        return 'Errors with changing amount'


def payment_operation(pay_to_book):
    token = get_credentials()
    if token:
        txid = get_random_string(35)
        if qr_code := get_qr_code(pay_to_book, txid, token):
            return qr_code
