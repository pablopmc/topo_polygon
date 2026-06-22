========================================================================
                      TOPOCALC - MANUAL E SOBRE
========================================================================

Este arquivo contém todas as informações pertinentes do software TopoCalc, 
mesclando o manual técnico de utilização e os metadados do sistema.

------------------------------------------------------------------------
1. SOBRE O SISTEMA
------------------------------------------------------------------------

Nome do Software: Sistema de Topografia Computacional TopoCalc
Release: Alpha v0.2.0
Data: 21 de junho de 2026
Autor: Pablo Medina Camacho
Email: pablo@pablomc.com
Curso: Engenharia Civil Empresarial
Instituição: Universidade Federal do Rio Grande (FURG)
Linguagem: Python (PySide6 + bibliotecas científicas)
Licença: Uso acadêmico e não comercial (similar à CC BY-NC 4.0)

Objetivo:
"Sistema desenvolvido para cálculos de fechamento topográficos, exclusivo 
para poligonais fechadas."

------------------------------------------------------------------------
2. MANUAL DE UTILIZAÇÃO ("COMO UTILIZAR")
------------------------------------------------------------------------

O TopoCalc é uma ferramenta desenvolvida para agilizar e dar precisão aos 
seus cálculos de poligonais topográficas. Este manual técnico orienta você 
sobre a inserção de dados, cálculos, consistência do projeto e exportação 
de resultados.

A) ENTRADA DE DADOS
===================
* Inserção de Vértices: Utilize o painel lateral ou o menu correspondente 
  para adicionar novos vértices. Cada vértice requer um nome identificador 
  único (ex: V1, V2), o ângulo horizontal observado, a distância horizontal 
  entre as estações e, opcionalmente, uma observação de campo.
* Formato de Coordenadas: O sistema utiliza coordenadas cartesianas planas 
  (Leste/X, Norte/Y). A coordenada inicial do primeiro vértice é arbitrada 
  como (0.0, 0.0) para cálculo interno e propagação relativa de toda a 
  poligonal.
* Inserção de Ângulos (DMS): Os ângulos de deflexão ou ângulos internos devem 
  ser informados no formato sexagesimal (Graus, Minutos e Segundos). O 
  sistema impõe restrições para minutos e segundos, que devem estar no 
  intervalo de 0 a 59.

B) CÁLCULOS DISPONÍVEIS
=======================
O TopoCalc executa de forma automática e integrada as seguintes operações:
* Azimutes: Calculados a partir da orientação inicial (azimute de partida) 
  informada pelo usuário e propagados consecutivamente vértice a vértice.
* Rumos: Derivados diretamente dos azimutes calculados, apresentando a 
  direção angular do alinhamento em relação aos eixos cardeais acompanhados 
  de seus respectivos quadrantes (NE, SE, SW, NW).
* Projeções Planas (Deltas): Decomposição trigonométrica dos alinhamentos em 
  coordenadas parciais não corrigidas:
    Delta X = Distância * sen(Azimute)
    Delta Y = Distância * cos(Azimute)
* Coordenadas Planimétricas: Determinação das coordenadas globais acumuladas 
  X (E) e Y (N) para cada vértice a partir do ponto de partida.
* Área pelo Método de Gauss: Cálculo exato da área de projeção do polígono 
  fechado baseado nas coordenadas cartesianas dos vértices.
* Perímetro: Somatório de todas as distâncias horizontais dos alinhamentos.
* Erro de Fechamento Angular: Diferença entre a soma observada dos ângulos 
  internos e a soma teórica calculada por (N - 2) * 180°, onde N é o número 
  de vértices.
* Erro de Fechamento Linear: Distância geométrica de fechamento obtida pela 
  resultante dos desvios lineares acumulados nos eixos X e Y: 
  Raiz_Quadrada(Dx² + Dy²).
* Ajuste pelo Método de Bowditch: Distribuição compensatória e proporcional 
  do erro de fechamento linear ao longo das distâncias horizontais de cada 
  alinhamento, corrigindo as projeções e gerando coordenadas ajustadas.

C) FORMATOS DE EXPORTAÇÃO
==========================
Os dados processados podem ser exportados para diferentes ferramentas:
* CSV: Exportação tabular em formato simples. Permite escolher o separador de 
  colunas (vírgula ou ponto e vírgula), ideal para importação em planilhas.
* DXF (AutoCAD): Desenho vetorial bidimensional contendo as linhas da 
  poligonal desenhadas, os marcadores de vértice e os rótulos de nomes.
* Excel (XLSX): Planilha formatada contendo as abas organizadas com dados de 
  entrada, cálculos de projeções e coordenadas e o resumo estatístico final.
* GeoJSON: Formato padrão GIS para representação de feições geográficas 
  vetoriais (pontos e linhas), facilitando a integração em softwares como QGIS.
* KML: Arquivo XML com os vértices e alinhamentos georreferenciados para 
  visualização tridimensional direta no Google Earth.
* Shapefile (SHP): Formato GIS composto pelos arquivos auxiliares necessários, 
  exportando as geometrias de pontos e polígonos com tabelas de atributos.
* PDF (Relatório Técnico): Relatório oficial formatado contendo dados do projeto, 
  tabelas completas de cálculo, fechamentos angulares e lineares e a 
  representação gráfica da poligonal (croqui).

D) IMPORTAÇÃO DE DADOS E ESTRUTURA DO ARQUIVO CSV
=================================================
* Arquivos Suportados: Planilhas do Excel (.xlsx, .xlsm) ou arquivos de texto 
  delimitados (.csv).
* Formato Esperado: A tabela deve conter cabeçalhos mapeados com nomes de colunas 
  válidos. O sistema suporta separadores de campo como ponto e vírgula (;) ou 
  vírgula (,) e trata decimais com pontos ou vírgulas.
* Mapeamento Flexível de Colunas (sinônimos aceitos):
  - Ponto / Vértice: ponto, point, point name, nome do ponto, vertex, vertice, 
                     estacao, estação, est, station
  - Ângulo Graus: graus, g, grau, angulo grau, deg, degrees
  - Ângulo Minutos: minutos, m, min, angulo minuto, minutes
  - Ângulo Segundos: segundos, s, sec, angulo segundo, seconds
  - Ângulo Decimal: angulo decimal, angulo, angulo_decimal, angle_decimal
  - Distância (m): distancia, distance, distância, comprimento, dist, len, length
  - Observações: observacao, observação, notes, nota, comentario, obs, observacoes
* Limitações: A importação substitui todos os dados atuais na tabela de trabalho.

E) CONVERSÃO DE ARQUIVOS GRANDES VIA INTELIGÊNCIA ARTIFICIAL
============================================================
Caso você possua dados brutos de campo extensos ou em formatos de texto 
proprietários desordenados, utilize o seguinte prompt em ferramentas de IA 
(como ChatGPT, Gemini ou Claude) para gerar seu CSV de importação instantaneamente:

--- INÍCIO DO PROMPT PARA IA ---
Você é um assistente especialista em topografia. Preciso que converta os dados brutos de campo fornecidos a seguir em um formato CSV limpo estruturado para o software TopoCalc.

Instruções:
1. O delimitador deve ser ponto e vírgula (;).
2. Cabeçalho exato: Ponto;Graus;Minutos;Segundos;Distancia;Observacao
3. Identifique os ângulos e separe-os em Graus, Minutos e Segundos. Se forem decimais, converta-os para GMS.
4. Isole as distâncias horizontais (sem letras ou unidades). Use o ponto (.) como separador decimal para distância e segundos.
5. Retorne APENAS o código do arquivo CSV, sem explicações adicionais ou marcações explicativas.

Dados para converter:
[INSIRA SEUS DADOS AQUI]
---- FIM DO PROMPT PARA IA ----

F) VALIDAÇÃO AUTOMÁTICA
=======================
O TopoCalc possui um sistema de verificação de consistência em tempo real:
* Avisos e Erros: A aba "Validação" exibe mensagens automáticas. Avisos apontam 
  inconsistências leves que não impedem a execução (ex: descrição do projeto 
  em branco). Erros críticos bloqueiam a execução de cálculos e exportações 
  (ex: menos de 3 vértices no polígono, nomes de vértices duplicados, valores 
  de minutos/segundos inválidos ou distâncias negativas).
* Rastreabilidade: Clique em qualquer mensagem de erro na lista de validação 
  para selecionar automaticamente a célula correspondente na tabela de dados e 
  destacá-la na área de desenho.

G) RELATÓRIOS EM PDF
====================
* Modelos Disponíveis (A3 vs A4): O modelo A4 Retrato é otimizado para 
  relatórios técnicos encadernados de várias páginas. O modelo A3 Paisagem 
  é ideal para visualização em folha única contendo o desenho da poligonal 
  em escala ampliada e tabelas completas.
* Seleção de Campos: Ao exportar para PDF, uma janela permite que você marque 
  quais dados devem constar no documento final (dados cadastrais, tabelas de 
  cálculo, resumo estatístico e croqui).

H) INTERFACE E NAVEGAÇÃO
========================
* Função dos Botões Principais:
  - Novo: Cria um novo projeto .topo solicitando identificação e local de salvamento.
  - Abrir: Carrega um projeto .topo salvo do disco.
  - Importar CSV/Excel: Importa em lote uma caderneta topográfica externa.
  - Salvar / Salvar Como: Salva o projeto no local atual ou sob novo nome.
  - Calcular: Executa o processamento matemático completo.
  - Atalhos de Exportação: Atalhos na barra para exportação rápida (CSV, DXF, 
    XLSX, GeoJSON, KML, SHP, PDF).
* Navegação entre Abas:
  - Vértices: Caderneta de entrada para digitação de ângulos e distâncias.
  - Ângulos: Exibição dos ângulos horizontais lidos e compensados.
  - Azimutes / Rumos: Orientação calculada para cada alinhamento.
  - Projeções / Coordenadas: Resultados espaciais e parciais antes e após o 
    ajuste de Bowditch.
  - Validação: Relatório de conformidade de integridade do projeto.

I) ARQUIVOS DE EXEMPLO
========================
* Arquivos exemplos disponíveis na pasta de instalação!