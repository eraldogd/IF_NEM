# 🎓 Gestão de Percursos 2026 — Streamlit App

Sistema de inscrição e acompanhamento de alunos em percursos/trilhas.

---

## ✅ Funcionalidades

- **Painel principal** com cards de vagas por curso (com cores: verde = livre, vermelho = lotado)
- **Filtro por Trilha** (TR1, TR2, TR3 ou TODAS)
- **Filtro por Curso** clicando nos cards
- **Busca** por nome ou matrícula
- **Matrícula de aluno** em curso via select
- **Limpar curso** de um aluno
- **Marcar/Desfazer Transferência**
- **Editar aluno** (matrícula, nome, turma, menção, TR)
- **Excluir aluno** com confirmação
- **Adicionar novo aluno**
- **Sorteio automático** com peso (prioriza turmas menos cheias)
- **Listas por Turma** e **por Professor** com download CSV
- **Dados salvos diretamente** no Google Sheets (compartilhado entre todos)

---

## 🚀 Como publicar no Streamlit Cloud (GRATUITO)

### Passo 1 — Prepare a Conta de Serviço Google

1. Acesse https://console.cloud.google.com
2. Crie um projeto (ex: "gestao-percursos")
3. No menu, vá em **APIs e Serviços → Biblioteca**
4. Ative: **Google Sheets API** e **Google Drive API**
5. Vá em **IAM e Administrador → Contas de Serviço**
6. Clique em **Criar Conta de Serviço**
   - Nome: `gestao-percursos`
   - Clique em **Concluído**
7. Clique na conta criada → aba **Chaves** → **Adicionar chave → JSON**
8. Baixe o arquivo `.json`

### Passo 2 — Compartilhe a Planilha

1. Abra sua planilha Google Sheets
2. Clique em **Compartilhar**
3. Cole o e-mail da conta de serviço (termina com `@*.iam.gserviceaccount.com`)
4. Dê permissão de **Editor**

### Passo 3 — Suba o código no GitHub

1. Crie uma conta em https://github.com (se não tiver)
2. Crie um repositório novo (ex: `gestao-percursos`)
3. Faça upload dos arquivos:
   - `app.py`
   - `requirements.txt`
   - (NÃO suba o arquivo `secrets.toml` — ele fica só no Streamlit Cloud)

### Passo 4 — Deploy no Streamlit Cloud

1. Acesse https://share.streamlit.io
2. Faça login com sua conta Google ou GitHub
3. Clique em **New app**
4. Selecione seu repositório e o arquivo `app.py`
5. Clique em **Advanced settings → Secrets**
6. Cole o conteúdo do arquivo `secrets.toml` preenchido com seus dados reais
7. Clique em **Deploy!**

Em ~2 minutos seu app estará online com uma URL pública como:
`https://seu-usuario-gestao-percursos.streamlit.app`

---

## 💻 Rodar localmente

```bash
# Instale as dependências
pip install -r requirements.txt

# Configure os secrets
# Crie a pasta .streamlit e edite o arquivo secrets.toml com seus dados reais

# Rode o app
streamlit run app.py
```

---

## 📋 Estrutura da Planilha

### Planilha1 (Alunos)
| Col A | Col B | Col C | Col D | Col E | Col F | Col G | Col H | Col I |
|-------|-------|-------|-------|-------|-------|-------|-------|-------|
| Matrícula | Nome | Turma | Menção | Ranking | Escolha (curso) | Prof Terça | Prof Quarta | TR |

### Planilha2 (Cursos)
| Col A | Col B | Col C | ... | Col H | Col I |
|-------|-------|-------|-----|-------|-------|
| TR | Código | Nome | ... | Prof Terça | Prof Quarta |

---

## ⚙️ Configurações

- Limite de vagas por curso: **35** (altere `VAGAS_MAX` no `app.py`)
- Cache de dados: **15 segundos** para alunos, **30 segundos** para cursos
- Clique em **🔄 Atualizar** para forçar recarga dos dados
