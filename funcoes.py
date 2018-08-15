from tika import parser
import re
import pandas as pd


def parsear_caderno_segunda(caderno):
    raw = parser.from_file(caderno)
    #remove quebras de páginas
    reg_quebra_pagina = re.compile('(\\n){4}Publicação Oficial do Tribunal de Justiça do Estado de São Paulo - Lei Federal nº 11.419/06, art. 4º(\\n){2}Disponibilização:.*?(\\n){2}')
    conteudo_pdf = reg_quebra_pagina.sub(' ', raw['content'])
    #quebra o documento pdf em uma lista de processos onde cada elemento é o conteúdo de um processo
    regex_processos = re.compile('(?<=Nº )\d{7}-\d{2}.\d{4}.\d.\d{2}.\d{4}.*?(?=\\n\\n|Nº)', re.DOTALL)
    lista_processos = regex_processos.findall(conteudo_pdf)
    
    ##EXTRACAO DE ENTIDADES DOS PROCESSOS###
    
    regex_processo = re.compile(r'\d{7}-\d{2}.\d{4}.\d.\d{2}.\d{4}', re.DOTALL)
    regex_parte_ativa = re.compile(r'(?<=Apelante:).*?(?=-)|(?<=Requerente:).*?(?=-)|(?<=Agravante:).*?(?=-)', re.DOTALL)
    regex_parte_passiva = re.compile(r'(?<=Apelad[o|a]:).*?(?=-)|(?<=Requeri[o|a]:).*?(?=-)|(?<=Agravad[o|a]:).*?(?=-)', re.DOTALL)
    regex_parte_neutra = re.compile(r'(?<=Apd[o|a]\/Apte:).*?(?=-)|(?<=Apte\/Apd[o|a]:).*?(?=-)')
    regex_advogados = re.compile(r'(?<=Advs:).*|(?<=Advogad[o|a]:).*', re.DOTALL)

    lista_apelacoes_danos_morais = []

    for i, processo in enumerate(lista_processos, 0):
        if re.search('- Apelação -', processo, 
                     re.MULTILINE) != None and re.search('danos morais', 
                                                         processo.lower(),
                                                         re.MULTILINE) != None:        
            try:            
                codigo_processo = regex_processo.search(processo).group(0)
                lista_ativos = regex_parte_ativa.findall(processo)
                lista_passivos = regex_parte_passiva.findall(processo)
                lista_advogados = regex_advogados.findall(processo)
                lista_neutros = regex_parte_neutra.findall(processo)

                conteudo = re.sub('\n', '', processo, re.MULTILINE)
                conteudo = re.sub(';', ' - ', conteudo, re.MULTILINE)
                conteudo = re.sub(r'\d{7}-\d{2}.\d{4}.\d.\d{2}.\d{4}', '', conteudo, re.DOTALL)
                conteudo = re.sub(r'(Apelante:.*?- |Requerente:.*?- )', '', conteudo, re.DOTALL)
                conteudo = re.sub(r'(Apelad[o|a]:.*?- |Requeri[o|a]:.*?- )', '', conteudo, re.DOTALL)
                conteudo = re.sub(r'(Advs:.*|Advogad(o|a):.*)', '', conteudo, re.DOTALL)
                conteudo = re.sub(r'(Apd(o|a)\/Apte:).*?-|(Apte\/Apd(o|a):).*?-', '', conteudo, re.DOTALL)

                lista_hifen = conteudo.split(' - ')
                meio_processo = lista_hifen[1]
                natureza_processo = lista_hifen[2]
                comarca = lista_hifen[3]

                conteudo = re.sub('- ' + lista_hifen[1] + ' - ', '', conteudo, re.DOTALL)
                conteudo = re.sub(lista_hifen[2] + ' - ', '', conteudo, re.DOTALL)
                conteudo = re.sub(lista_hifen[3] + ' - ', '', conteudo, re.DOTALL)

                tupla = (codigo_processo, 
                         meio_processo, 
                         natureza_processo, 
                         comarca,
                         ' '.join(lista_ativos),
                         ' '.join(lista_passivos),                     
                         ' '.join(lista_neutros),
                         ' '.join(lista_advogados),
                         conteudo,
                         processo)
                lista_apelacoes_danos_morais.append(tupla)
            except:            
                print('erro na extração de entidades do processo {}'.format(codigo_processo))
    
    df = pd.DataFrame.from_records(lista_apelacoes_danos_morais)
    df.columns = ['codigo_processo', 'meio_processo', 'natureza_processo', 'comarca','lista_ativos','lista_passivos', 'lista_neutros', 'lista_advogados','conteudo', 'texto_original']
    return df