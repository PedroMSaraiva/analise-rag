#!/usr/bin/env python3
"""
Script para geração de benchmark baseado em contextos.

Este script recebe uma lista de contextos (parágrafos sobre robótica educacional)
e gera 5 perguntas diferentes para cada contexto, salvando os resultados em CSV.
"""

import csv
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import logging
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from api_llm.utils.extra_functions import get_model
from dotenv import load_dotenv

load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextBasedBenchmarkGenerator:
    def __init__(self, output_dir: str = "benchmarks"):
        """
        Inicializa o gerador de benchmark baseado em contextos.
        
        Args:
            output_dir: Diretório onde salvar os resultados
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.model = get_model(temperature=0.7)
        self.contexts = []
        self.benchmark_data = []
        
        # Prompt para geração de perguntas
        self.question_generation_prompt = """
Você é um especialista em robótica educacional e criação de materiais pedagógicos.

CONTEXTO FORNECIDO:
{context}

TAREFA:
Baseado no contexto acima, gere EXATAMENTE 5 perguntas diferentes que um aluno ou professor poderia fazer sobre este tópico. As perguntas devem:

1. Ser específicas e relevantes ao contexto fornecido
2. Variar em níveis de dificuldade (básica, intermediária, avançada)
3. Abordar diferentes aspectos do tópico (conceitual, prático, aplicação)
4. Ser claras e bem formuladas
5. Estar relacionadas ao ensino de robótica educacional

FORMATO DE RESPOSTA:
Responda APENAS com as 5 perguntas, uma por linha, numeradas de 1 a 5.

Exemplo:
1. Como funciona um sensor ultrassônico em projetos de robótica?
2. Qual é a diferença entre sensores digitais e analógicos?
3. Como programar um Arduino para ler dados de sensores?
4. Quais são as principais aplicações de sensores em robótica educacional?
5. Como calibrar um sensor de temperatura para obter medições precisas?

SUAS 5 PERGUNTAS:
"""

    def load_contexts_from_list(self, contexts_list: List[str]):
        """
        Carrega contextos de uma lista fornecida.
        
        Args:
            contexts_list: Lista de strings com os contextos
        """
        self.contexts = []
        for i, context in enumerate(contexts_list, 1):
            self.contexts.append({
                'id': i,
                'context': context.strip(),
                'category': 'robotica_educacional',
                'source': 'manual'
            })
        
        print(f"✅ Carregados {len(self.contexts)} contextos da lista fornecida")

    def load_contexts_from_file(self, file_path: str):
        """
        Carrega contextos de um arquivo (JSON ou TXT).
        
        Args:
            file_path: Caminho para o arquivo com contextos
        """
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.contexts = [{'id': i+1, 'context': ctx, 'category': 'robotica_educacional', 'source': 'file'} 
                                       for i, ctx in enumerate(data)]
                    elif isinstance(data, dict):
                        self.contexts = [{'id': i+1, 'context': ctx['context'], 
                                        'category': ctx.get('category', 'robotica_educacional'),
                                        'source': 'file'} 
                                       for i, ctx in enumerate(data.get('contexts', []))]
            
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Divide por linhas vazias ou marcadores como "---"
                    contexts = [ctx.strip() for ctx in content.split('\n\n') if ctx.strip()]
                    self.contexts = [{'id': i+1, 'context': ctx, 'category': 'robotica_educacional', 'source': 'file'} 
                                   for i, ctx in enumerate(contexts)]
            
            print(f"✅ Carregados {len(self.contexts)} contextos do arquivo {file_path}")
            
        except Exception as e:
            print(f"❌ Erro ao carregar contextos do arquivo: {e}")
            return False
        
        return True

    def get_default_contexts(self) -> List[str]:
        """
        Retorna uma lista de contextos padrão sobre robótica educacional.
        
        Returns:
            Lista de contextos de exemplo
        """
        default_contexts = [
            """Arduino Uno é uma placa de microcontrolador baseada no ATmega328P. Possui 14 pinos de entrada/saída digital (dos quais 6 podem ser usados como saídas PWM), 6 entradas analógicas, um cristal de 16 MHz, conexão USB, conector de alimentação, header ICSP e botão de reset. O Arduino Uno é uma das placas mais populares para iniciantes em robótica educacional devido à sua simplicidade e ampla documentação disponível. A programação é feita através da IDE Arduino, que utiliza uma linguagem baseada em C/C++. A placa pode ser alimentada via USB ou fonte externa e possui proteções contra sobrecorrente.""",
            
            """Motores DC são componentes fundamentais em projetos de robótica educacional. Eles convertem energia elétrica em energia mecânica através do movimento rotativo. O controle de velocidade pode ser feito através de PWM (Pulse Width Modulation), onde a largura do pulso determina a velocidade do motor. Para controlar a direção do movimento, utiliza-se uma ponte H, que permite inverter a polaridade da tensão aplicada ao motor. Motores DC são amplamente utilizados em robôs móveis, braços robóticos e projetos de automação devido à sua simplicidade de controle e boa relação custo-benefício.""",
            
            """Sensores ultrassônicos são dispositivos que medem distância através da emissão de ondas sonoras de alta frequência. O sensor HC-SR04 é um dos mais utilizados em robótica educacional. Ele possui quatro pinos: VCC (alimentação), GND (terra), Trig (trigger) e Echo. O funcionamento baseia-se no princípio do sonar: o sensor emite um pulso ultrassônico e mede o tempo que a onda leva para retornar após colidir com um obstáculo. A distância é calculada usando a fórmula: distância = (tempo × velocidade do som) / 2. Estes sensores são essenciais para robôs que precisam navegar autonomamente e evitar obstáculos.""",
            
            """LEDs (Light Emitting Diodes) são componentes semicondutores que emitem luz quando uma corrente elétrica passa através deles. Na robótica educacional, LEDs são utilizados para sinalização, feedback visual e criação de efeitos luminosos. Existem LEDs de diversas cores, incluindo vermelho, verde, azul, amarelo e branco. LEDs RGB podem produzir uma ampla gama de cores através da combinação das três cores primárias. É importante sempre utilizar resistores limitadores de corrente com LEDs para evitar danos ao componente. O cálculo do resistor é feito pela Lei de Ohm: R = (Vsource - Vled) / Iled.""",
            
            """Servo motores são atuadores precisos amplamente utilizados em robótica educacional para controle de posição angular. Diferentemente dos motores DC comuns, servo motores possuem controle de posição integrado através de um sistema de feedback com potenciômetro interno. O controle é feito através de sinais PWM com frequência de 50Hz, onde a largura do pulso (entre 1ms e 2ms) determina o ângulo de rotação. Servo motores padrão têm rotação limitada a aproximadamente 180 graus, sendo ideais para braços robóticos, direção de robôs e mecanismos que requerem posicionamento preciso.""",
            
            """Sensores de linha são dispositivos ópticos utilizados em robôs seguidores de linha. Consistem em um LED infravermelho emissor e um fototransistor ou LDR receptor. O funcionamento baseia-se na diferença de reflexão da luz infravermelha entre superfícies claras e escuras. Superfícies claras refletem mais luz infravermelha, enquanto superfícies escuras absorvem mais luz. Esta diferença é convertida em sinais elétricos que podem ser processados pelo microcontrolador. Robôs seguidores de linha utilizam arrays de sensores para detectar a posição da linha e ajustar sua trajetória através de algoritmos de controle PID.""",
            
            """Protoboards (matrizes de contato) são ferramentas essenciais para prototipagem rápida em eletrônica e robótica educacional. Permitem a montagem de circuitos sem soldagem, facilitando testes e modificações. Uma protoboard padrão possui furos organizados em fileiras e colunas, onde as conexões internas seguem um padrão específico. As fileiras centrais são conectadas horizontalmente, enquanto as linhas de alimentação (power rails) nas bordas são conectadas verticalmente. Esta organização permite a criação rápida de circuitos complexos. Componentes são inseridos nos furos e as conexões são feitas através de jumpers (fios de ligação).""",
            
            """Resistores são componentes eletrônicos passivos que limitam o fluxo de corrente elétrica em um circuito. Na robótica educacional, são utilizados para proteção de componentes, divisores de tensão e controle de corrente. O valor da resistência é indicado através de um código de cores com faixas pintadas no corpo do resistor. A leitura segue uma tabela específica onde cada cor representa um dígito ou multiplicador. Resistores também possuem tolerância, que indica a precisão do valor nominal. Para aplicações em robótica, resistores de 1/4W são suficientes para a maioria dos circuitos de baixa potência.""",
            
            """Comunicação I2C (Inter-Integrated Circuit) é um protocolo de comunicação serial amplamente utilizado em sistemas embarcados e robótica educacional. Utiliza apenas dois fios: SDA (Serial Data) para dados e SCL (Serial Clock) para sincronização. Múltiplos dispositivos podem ser conectados no mesmo barramento, cada um com um endereço único. O protocolo suporta diferentes velocidades de comunicação, sendo 100kHz (modo padrão) e 400kHz (modo rápido) as mais comuns. I2C é ideal para conectar sensores, displays LCD, módulos RTC e outros periféricos ao microcontrolador, reduzindo o número de pinos necessários.""",
            
            """Internet das Coisas (IoT) em robótica educacional permite a criação de robôs conectados capazes de comunicar-se através da internet. Módulos como ESP32 e ESP8266 integram Wi-Fi e permitem que robôs enviem dados para servidores remotos, recebam comandos via aplicativos móveis ou interajam com outros dispositivos conectados. Aplicações incluem monitoramento ambiental com sensores, controle remoto de robôs, coleta de dados para análise e integração com assistentes virtuais. A programação IoT envolve conceitos de redes, protocolos de comunicação (HTTP, MQTT) e segurança de dados."""
        ]
        
        # Adicionar contextos dos arquivos JSON
        json_contexts = self._load_contexts_from_json_files()
        default_contexts.extend(json_contexts)
        
        return default_contexts

    def _load_contexts_from_json_files(self) -> List[str]:
        """Carrega contextos dos arquivos JSON especificados."""
        json_files = [
            "rag_sys/material/2_livros_teorica/ROBOTICA_PTBR.json",
            "rag_sys/material/2_livros_teorica/EDUCAÇÃO EMPREENDEDORA_PTBR.json",
            "rag_sys/material/2_livros_teorica/ELETRICIDADE E ELETRÔNICA_PTBR.json",
            "rag_sys/material/2_livros_teorica/Remoção e colocação impressora 3D.json",
            "rag_sys/material/2_livros_teorica/ESTRUTURAS_PTBR.json"
        ]
        
        all_contexts = []
        
        for json_file in json_files:
            try:
                # Tentar encontrar o arquivo a partir da raiz do projeto
                current_path = Path(__file__).parent
                for _ in range(5):  # Procurar até 5 níveis acima
                    file_path = current_path / json_file
                    if file_path.exists():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            contexts = self._extract_contexts_from_json(data)
                            all_contexts.extend(contexts[:5])  # Limitar a 5 contextos por arquivo
                            logger.info(f"Carregados {len(contexts[:5])} contextos de {json_file}")
                        break
                    current_path = current_path.parent
                else:
                    logger.warning(f"Arquivo não encontrado: {json_file}")
            except Exception as e:
                logger.warning(f"Erro ao carregar {json_file}: {e}")
        
        return all_contexts

    def _extract_contexts_from_json(self, data: List[Dict]) -> List[str]:
        """Extrai contextos relevantes dos arquivos JSON educacionais."""
        contexts = []
        
        for item in data:
            # Adicionar conteúdo principal
            if 'content' in item:
                if isinstance(item['content'], list):
                    # Juntar itens da lista que são strings substantivas
                    content_text = ' '.join([
                        str(c) for c in item['content'] 
                        if isinstance(c, str) and len(c.strip()) > 50 and not c.strip().startswith('![')
                    ])
                    if content_text and len(content_text) > 100:
                        contexts.append(f"Tópico: {item.get('topic', 'Não especificado')}\n\n{content_text}")
                else:
                    content_text = str(item['content']).strip()
                    if len(content_text) > 100:
                        contexts.append(f"Tópico: {item.get('topic', 'Não especificado')}\n\n{content_text}")
            
            # Adicionar subtópicos se existirem
            if 'subtopics' in item and item['subtopics']:
                for subtopic in item['subtopics']:
                    if isinstance(subtopic, dict) and 'content' in subtopic:
                        if isinstance(subtopic['content'], list):
                            subcontent_text = ' '.join([
                                str(c) for c in subtopic['content'] 
                                if isinstance(c, str) and len(c.strip()) > 50 and not c.strip().startswith('![')
                            ])
                        else:
                            subcontent_text = str(subtopic['content']).strip()
                        
                        if subcontent_text and len(subcontent_text) > 100:
                            contexts.append(f"Subtópico: {subtopic.get('subtopic', 'Não especificado')}\n\n{subcontent_text}")
        
        return contexts

    async def generate_questions_for_context(self, context_data: Dict) -> List[Dict]:
        """
        Gera 5 perguntas para um contexto específico.
        
        Args:
            context_data: Dicionário com dados do contexto
            
        Returns:
            Lista de dicionários com as perguntas geradas
        """
        try:
            print(f"🤖 Gerando perguntas para contexto {context_data['id']}...")
            
            prompt = self.question_generation_prompt.format(context=context_data['context'])
            
            messages = [
                {"role": "system", "content": [{"type": "text", "text": "Você é um especialista em robótica educacional."}]},
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ]
            
            response = await self.model.ainvoke(messages)
            response_text = response.content if response and response.content else ""
            
            if not response_text:
                raise ValueError("Resposta vazia do modelo")
            
            # Processa a resposta para extrair as 5 perguntas
            questions = self._extract_questions(response_text)
            
            if len(questions) != 5:
                print(f"⚠️ Esperadas 5 perguntas, obtidas {len(questions)}. Tentando novamente...")
                # Tenta novamente com prompt mais específico
                return await self._retry_question_generation(context_data)
            
            # Cria lista de perguntas com metadados
            questions_data = []
            for i, question in enumerate(questions, 1):
                questions_data.append({
                    'context_id': context_data['id'],
                    'question_id': i,
                    'context': context_data['context'],
                    'question': question,
                    'category': context_data['category'],
                    'difficulty': self._estimate_difficulty(question),
                    'question_type': self._classify_question_type(question),
                    'source': context_data['source']
                })
            
            print(f"✅ Geradas {len(questions_data)} perguntas para contexto {context_data['id']}")
            return questions_data
            
        except Exception as e:
            print(f"❌ Erro ao gerar perguntas para contexto {context_data['id']}: {e}")
            return []

    def _extract_questions(self, response_text: str) -> List[str]:
        """
        Extrai as perguntas numeradas da resposta do modelo.
        
        Args:
            response_text: Texto da resposta do modelo
            
        Returns:
            Lista de perguntas extraídas
        """
        questions = []
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Procura por linhas que começam com número seguido de ponto ou parêntese
            if line and (line[0].isdigit() or line.startswith('*')):
                # Remove numeração e limpa a pergunta
                if '. ' in line:
                    question = line.split('. ', 1)[1].strip()
                elif ') ' in line:
                    question = line.split(') ', 1)[1].strip()
                elif line.startswith('* '):
                    question = line[2:].strip()
                else:
                    question = line.strip()
                
                if question and len(question) > 10:  # Filtro básico de qualidade
                    questions.append(question)
        
        return questions[:5]  # Garante máximo de 5 perguntas

    async def _retry_question_generation(self, context_data: Dict) -> List[Dict]:
        """
        Tenta gerar perguntas novamente com prompt mais específico.
        """
        try:
            retry_prompt = f"""
CONTEXTO: {context_data['context'][:500]}...

Gere EXATAMENTE 5 perguntas sobre este contexto. Formate sua resposta assim:

1. [Primeira pergunta aqui]
2. [Segunda pergunta aqui] 
3. [Terceira pergunta aqui]
4. [Quarta pergunta aqui]
5. [Quinta pergunta aqui]

Não adicione texto extra, apenas as 5 perguntas numeradas.
"""
            
            messages = [
                {"role": "user", "content": [{"type": "text", "text": retry_prompt}]}
            ]
            
            response = await self.model.ainvoke(messages)
            questions = self._extract_questions(response.content)
            
            # Se ainda não conseguiu 5, cria perguntas genéricas
            while len(questions) < 5:
                questions.append(f"Como aplicar os conceitos deste contexto em projetos práticos de robótica educacional? (Pergunta {len(questions)+1})")
            
            questions_data = []
            for i, question in enumerate(questions[:5], 1):
                questions_data.append({
                    'context_id': context_data['id'],
                    'question_id': i,
                    'context': context_data['context'],
                    'question': question,
                    'category': context_data['category'],
                    'difficulty': 'media',
                    'question_type': 'aplicacao',
                    'source': context_data['source']
                })
            
            return questions_data
            
        except Exception as e:
            print(f"❌ Erro na retry: {e}")
            return []

    def _estimate_difficulty(self, question: str) -> str:
        """
        Estima a dificuldade da pergunta baseada em palavras-chave.
        
        Args:
            question: Texto da pergunta
            
        Returns:
            Nível de dificuldade: 'basica', 'media' ou 'avancada'
        """
        question_lower = question.lower()
        
        # Palavras que indicam nível básico
        basic_keywords = ['o que é', 'como funciona', 'qual é', 'quais são', 'definir', 'explicar']
        # Palavras que indicam nível avançado
        advanced_keywords = ['otimizar', 'algoritmo', 'implementar', 'integrar', 'análise', 'calcular', 'programar']
        
        if any(keyword in question_lower for keyword in advanced_keywords):
            return 'avancada'
        elif any(keyword in question_lower for keyword in basic_keywords):
            return 'basica'
        else:
            return 'media'

    def _classify_question_type(self, question: str) -> str:
        """
        Classifica o tipo da pergunta.
        
        Args:
            question: Texto da pergunta
            
        Returns:
            Tipo da pergunta: 'conceitual', 'pratica' ou 'aplicacao'
        """
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['como fazer', 'como programar', 'como conectar', 'passo a passo']):
            return 'pratica'
        elif any(word in question_lower for word in ['aplicar', 'projeto', 'usar em', 'exemplo de uso']):
            return 'aplicacao'
        else:
            return 'conceitual'

    async def generate_benchmark(self, contexts_source=None):
        """
        Gera o benchmark completo baseado nos contextos.
        
        Args:
            contexts_source: Lista de contextos, caminho para arquivo ou None para usar padrão
        """
        print("🚀 INICIANDO GERAÇÃO DE BENCHMARK BASEADO EM CONTEXTOS")
        print("=" * 70)
        
        # Carrega contextos
        if isinstance(contexts_source, list):
            self.load_contexts_from_list(contexts_source)
        elif isinstance(contexts_source, str):
            if not self.load_contexts_from_file(contexts_source):
                return False
        else:
            print("📋 Usando contextos padrão de robótica educacional...")
            default_contexts = self.get_default_contexts()
            self.load_contexts_from_list(default_contexts)
        
        if not self.contexts:
            print("❌ Nenhum contexto carregado!")
            return False
        
        # Gera perguntas para cada contexto
        print(f"\n🤖 Gerando perguntas para {len(self.contexts)} contextos...")
        
        for context_data in self.contexts:
            questions_data = await self.generate_questions_for_context(context_data)
            self.benchmark_data.extend(questions_data)
            
            # Pequena pausa para evitar rate limiting
            await asyncio.sleep(1)
        
        print(f"\n✅ Geração concluída! Total: {len(self.benchmark_data)} perguntas")
        return True

    def save_benchmark(self, filename: str = None):
        """
        Salva o benchmark em arquivo CSV.
        
        Args:
            filename: Nome do arquivo (opcional)
        """
        if not self.benchmark_data:
            print("❌ Nenhum dado para salvar!")
            return False
        
        # Cria diretório se não existir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Nome do arquivo
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"context_based_benchmark_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as file:
                fieldnames = [
                    'context_id', 'question_id', 'context', 'question', 
                    'category', 'difficulty', 'question_type', 'source'
                ]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in self.benchmark_data:
                    writer.writerow(row)
            
            print(f"💾 Benchmark salvo em: {filepath}")
            print(f"📊 Total de registros: {len(self.benchmark_data)}")
            
            # Salva também em JSON para backup
            json_filepath = filepath.replace('.csv', '.json')
            with open(json_filepath, 'w', encoding='utf-8') as file:
                json.dump(self.benchmark_data, file, ensure_ascii=False, indent=2)
            
            print(f"💾 Backup JSON salvo em: {json_filepath}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar benchmark: {e}")
            return False

    def print_summary(self):
        """Imprime resumo estatístico do benchmark gerado."""
        if not self.benchmark_data:
            print("❌ Nenhum dado para resumir!")
            return
        
        print("\n" + "=" * 70)
        print("📊 RESUMO DO BENCHMARK GERADO")
        print("=" * 70)
        
        total_questions = len(self.benchmark_data)
        total_contexts = len(set(item['context_id'] for item in self.benchmark_data))
        
        print(f"📝 Total de contextos: {total_contexts}")
        print(f"❓ Total de perguntas: {total_questions}")
        print(f"📏 Média de perguntas por contexto: {total_questions/total_contexts:.1f}")
        
        # Estatísticas por dificuldade
        difficulties = {}
        for item in self.benchmark_data:
            diff = item['difficulty']
            difficulties[diff] = difficulties.get(diff, 0) + 1
        
        print(f"\n🎯 DISTRIBUIÇÃO POR DIFICULDADE:")
        for diff, count in difficulties.items():
            percentage = (count / total_questions) * 100
            print(f"   {diff.capitalize()}: {count} ({percentage:.1f}%)")
        
        # Estatísticas por tipo
        types = {}
        for item in self.benchmark_data:
            qtype = item['question_type']
            types[qtype] = types.get(qtype, 0) + 1
        
        print(f"\n📋 DISTRIBUIÇÃO POR TIPO:")
        for qtype, count in types.items():
            percentage = (count / total_questions) * 100
            print(f"   {qtype.capitalize()}: {count} ({percentage:.1f}%)")
        
        print("=" * 70)


async def main():
    """Função principal do script."""
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Erro: OPENAI_API_KEY não configurada")
        sys.exit(1)
    
    generator = ContextBasedBenchmarkGenerator()
    
    # Exemplo de uso com contextos padrão
    success = await generator.generate_benchmark()
    
    if success:
        generator.save_benchmark()
        generator.print_summary()
    else:
        print("❌ Falha na geração do benchmark")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 