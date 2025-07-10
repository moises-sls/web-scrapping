from bs4 import BeautifulSoup as bs
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException 

THE_url = "https://www.timeshighereducation.com/world-university-rankings/latest/world-ranking#!/length/100/sort_by/rank/sort_order/asc/cols/scores"

all_rows = []

driver = webdriver.Firefox()

driver.get(THE_url)

time.sleep(2)

####################################### Aceitando cookies ###################################
try:
    # Espera até que o botão de aceitar todos os cookies esteja visível e clicável
    # esse é o ID para o botao de aceitar todos os cookies
    cookie_accept_button = WebDriverWait(driver, 1).until(
        EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
    )
    cookie_accept_button.click()
    print("Cookies aceitos com sucesso!")
    time.sleep(0.5)
except Exception as e:
    print(f"Não foi possível interagir com o pop-up de cookies ou ele não apareceu: {e}")

#################################### Pegando as colunas da tabela ##################################

# pegando o html da página atual
content = driver.page_source
soup = bs(content, "html.parser")

tabela = soup.find(id='datatable-1')

columns = tabela.find("thead").find("tr").find_all("th")

col_names = [c.string for c in columns]

####################################################################################################

###################################### Navegando pelas páginas #####################################

page_number = 1

while True:

    try:
        ###################### Pegando os dados da tabela #########################
        # atualizando o link do html para conseguir extrair os dados de cada página
        content = driver.page_source
        soup = bs(content, "html.parser")

        tabela = soup.find(id='datatable-1')
        rows = tabela.find("tbody").find_all("tr")
        for row in rows:
            row_data = [data.get_text(strip=True) for data in row.find_all("td")]
            all_rows.append(row_data) 

        ##########################################################################


        #################### Navegando para próxima página #######################
        # Localiza o elemento pai do botão "Próxima Página" (<li> é o pai; <a> (link) é o filho)
        # O seletor é para o <li> que contém o <a> do botão "Next"
        next_page_parent = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.ID, "datatable-1_next"))
        )

        # Verifica se a classe 'disabled' está presente no elemento pai
        # Se estiver, significa que estamos na última página
        if "disabled" in next_page_parent.get_attribute("class"):
            print(f"Chegou à última página (Página {page_number}). Encerrando o programa.")
            break # Sai do loop

        # Se não estiver desativado, localiza o botão de clique dentro do pai (procurando o <a> (link))
        next_page_button = next_page_parent.find_element(By.TAG_NAME, "a")


        # scrollamos para baixo até o elemento next_page_button estar visível
        driver.execute_script("arguments[0].scrollIntoView(true);", next_page_button)
        time.sleep(0.5) # Pequena pausa para a rolagem ocorrer

        # clicamos no botão
        driver.execute_script("arguments[0].click();", next_page_button)
        page_number += 1
        print(f"Clicou na próxima página (Página {page_number}).")
        time.sleep(1) # Pausa para o carregamento da próxima página

    except (NoSuchElementException, TimeoutException) as e:
        # Se o botão não for encontrado ou houver timeout, pode ser a última página
        # ou algum outro problema. Imprime o erro e tenta sair.
        print(f"Erro ou botão 'Próxima Página' não encontrado após a Página {page_number}. Pode ser a última página ou um erro inesperado: {e}")
        break
    except Exception as e:
        print(f"Ocorreu um erro inesperado na Página {page_number}: {e}")
        break

print("Navegação concluída.")
driver.quit() # Fecha o navegador ao final


dados = pd.DataFrame(all_rows, columns=col_names)
dados = dados.rename(columns = {None : "University Name"})

# Corrigindo o nome das universidades:
padrao_regex = r'([a-z])([A-Z])' # busca quando uma letra minuscula é imediatamente seguida de uma letra
# maiuscula, por exemplo: University of OxfordUnited Kingdom
# o padrao vai encontrar OxfordUnited, com: Oxfor "d" -> (primeiro grupo de captura) 
# e "U" nited -> (segundo grupo de captura)
# o parentese permite referenciar esses grupos de captura
# 
# substituiremos a ocorrencia desse padrao_regex por r' \1 \2', ou seja, quando esse padrao ocorrer
# a primeira letra(minuscula) é mantida, depois é seguida por um espaço em branco, e a segunda 
# letra(maiuscula) é inserida

dados['University Name'] = dados['University Name'].str.replace(padrao_regex, r'\1 \2', regex=True)


dados.to_excel('the_global_2025.xlsx', index=False)