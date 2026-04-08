# Tailwind CSS v4 — Native Binding em Linux

## The Insight
`@tailwindcss/vite` v4+ usa `@tailwindcss/oxide` com binário nativo (.node). No Linux, o npm não instala o binding correto automaticamente quando há conflito de plataforma no lockfile. Limpar node_modules e reinstalar não resolve — é preciso instalar o pacote de plataforma explicitamente.

## Why This Matters
O erro `Cannot find native binding` bloqueia o `vite dev` completamente, e a mensagem de erro sugere apenas `rm node_modules && npm i`, que não funciona.

## Recognition Pattern
- Stack: Vite + `@tailwindcss/vite` ^4.x + Node 18 no Linux
- Erro: `Error: Cannot find native binding` em `node_modules/@tailwindcss/oxide/index.js`
- `ls node_modules/@tailwindcss/oxide/*.node` retorna vazio

## The Approach
Após `rm -rf node_modules package-lock.json && npm install`, se o erro persistir:

```bash
npm install @tailwindcss/oxide-linux-x64-gnu
```

Isso força a instalação do binding correto para Linux x64. O Vite sobe normalmente após isso.

## Files
- `eventnexus-frontend/` — contexto onde o problema ocorreu (Node 18, Linux x64)
