import requests
from flask import Flask, request


app = Flask(__name__)

# Estrutura para armazenar os dados do atendimento
atendimento_data = {}

def check_token():
    url = "https://crm.rdstation.com/api/v1/token/check?token=6500668a21ce0e000f228a06"
    headers = {
        "Authorization": "6500668a21ce0e000f228a06",
        "accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("Token válido!")
        print(response.text)
    else:
        print(f"Erro ao verificar o token: {response.status_code}, {response.text}")

def check_contact(chat_id, cliente_numero):
    print("Função check_contact foi chamada.")  # Adicione este print
    url = f"https://crm.rdstation.com/api/v1/contacts?token=6500668a21ce0e000f228a06&limit=200&phone={cliente_numero}"
    print(f"URL da API do RD Station CRM: {url}")  # Adicione este print
    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)
    print(f"Resposta da API do RD Station CRM: {response.status_code}, {response.text}")

    if response.status_code == 200:
        data = response.json()
        if data['contacts']:
            print(f"Contato com o número {cliente_numero} encontrado no RD Station CRM.")
            # Aqui você pode adicionar o código para alterar o campo de anotações do CRM
            # ...
        else:
            print(f"Contato com o número {cliente_numero} não encontrado no RD Station CRM.")
            create_deal(atendimento_data[chat_id]['cliente_nome'], cliente_numero)
    else:
        print(f"Erro ao verificar o contato: {response.status_code}, {response.text}")

def create_deal(cliente_nome, cliente_numero):
    url = "https://crm.rdstation.com/api/v1/deals?token=6500668a21ce0e000f228a06"
    headers = {
        "Authorization": "Bearer 6500668a21ce0e000f228a06",
        "accept": "application/json",
        "content-type": "application/json"
    }
    payload = {
        # ...
        "contacts": [
            {
                # ...
                "name": cliente_nome,
                "phones": [
                    {
                        "phone": cliente_numero,
                        "type": "cellphone"
                    }
                ],
                # ...
            }
        ],
        "deal": {
            # ...
            "name": cliente_nome,
            # ...
        },
        # ...
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        deal_data = response.json()
        deal_id = deal_data.get("_id")  # Obtenha a ID da negociação criada
        print(f"Negociação para o contato {cliente_nome} criada com sucesso no RD Station CRM. ID da negociação: {deal_id}")
        return deal_id  # Retorne a ID da negociação
    else:
        print(f"Erro ao criar a negociação: {response.status_code}, {response.text}")
        return None



def create_annotation(deal_id, annotation_text):
    url = f"https://crm.rdstation.com/api/v1/deals/{deal_id}/annotations?token=6500668a21ce0e000f228a06"
    headers = {
        "Authorization": "Bearer 6500668a21ce0e000f228a06",
        "accept": "application/json",
        "content-type": "application/json"
    }
    payload = {
        "deal_id": deal_id,
        "text": annotation_text,
        "type": "note"  # Tipo de anotação (pode ser personalizado)
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        annotation_data = response.json()
        annotation_id = annotation_data.get("_id")  # Obtenha a ID da anotação criada
        print(f"Anotação criada com sucesso. ID da anotação: {annotation_id}")
        return annotation_id  # Retorne a ID da anotação
    else:
        print(f"Erro ao criar a anotação: {response.status_code}, {response.text}")
        return None


@app.route('/', methods=['POST'])
def webhook_listener():
    data = request.json
    print(data)  # Imprime os dados da solicitação

    if data.get('event_type') == 'atendimento_iniciado':
        chat_id = data['attendance']['attendanceNumber']
        # Coleta apenas o nome do cliente e o número de telefone
        cliente_nome = data['attendance']['customer']['name']
        cliente_numero = data['attendance']['customer']['phone']
        check_contact(chat_id, cliente_numero)

        atendimento_data[chat_id] = {
            'cliente_nome': cliente_nome,
            'cliente_numero': cliente_numero,
            'conversas': []  # Inicialize a lista de conversas vazia
        }
        print(f"Atendimento {chat_id} iniciado. Dados salvos: {atendimento_data[chat_id]}")

        check_contact(chat_id, cliente_numero)

    elif data.get('event_type') == 'atendimento_encerrado':
        chat_id = data['attendance']['attendanceNumber']
        # Atualiza as conversas com as mensagens finais
        atendimento_data[chat_id]['conversas'] = data['chat']  # Substitua as conversas pelo novo conjunto de mensagens

        # Obtenha todas as informações relevantes do atendimento
        cliente_nome = atendimento_data[chat_id]['cliente_nome']
        conversas = "\n".join(atendimento_data[chat_id]['conversas'])
        atendente = data['attendance']['finishBy']
        hora_inicio = data['attendance']['startTime']
        hora_final = data['attendance']['endTime']
        relato_operador = data['attendance']['operatorReport']
        departamento = data['attendance']['departament']

        # Crie o texto da anotação com todas as informações
        annotation_text = f"Atendimento para {cliente_nome} encerrado.\n"
        annotation_text += f"Atendente: {atendente}\n"
        annotation_text += f"Hora de início: {hora_inicio}\n"
        annotation_text += f"Hora de finalização: {hora_final}\n"
        annotation_text += f"Relato do operador: {relato_operador}\n"
        annotation_text += f"Departamento: {departamento}\n"
        annotation_text += f"Conversa do atendimento:\n{conversas}"

        print(f"Atendimento {chat_id} encerrado. Dados finais: {atendimento_data[chat_id]}")

        # Após o encerramento do atendimento, crie a anotação com o texto criado
        deal_id = atendimento_data[chat_id].get('deal_id')
        if deal_id:
            create_annotation(deal_id, annotation_text)

    return 'OK'

def update_webhooks():
    url = "https://www.plugchat.com.br/api/integrations/update-webhooks"
    headers = {
        "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdhbml6YXRpb25JZCI6IjE2NmJhODM3LThiNTctNDkwYy1hZDFiLWEwZGFmZWI5ZGFiNyIsImlhdCI6MTY5NTA0MzE5NSwiZXhwIjo0ODQ5MDQzMTk1fQ.XTOGVenB6bUcEda7UhXQB10ELpC8suRcTBzSxVrkrU4",
        "Content-Type": "application/json"
    }
    data = {
        "finishAttendance": "http://127.0.0.1:5000",
        "startAttendance": "http://127.0.0.1:5000",
    }
    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        print("Webhooks atualizados com sucesso!")
    else:
        print(f"Erro ao atualizar webhooks: {response.status_code}, {response.text}")


if __name__ == '__main__':
    check_token()
    update_webhooks()


