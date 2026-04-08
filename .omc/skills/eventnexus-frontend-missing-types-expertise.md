# eventnexus-frontend: Pacotes @types Ausentes

## The Insight
O projeto `eventnexus-frontend` foi criado sem `@types/react` e `@types/react-dom` nas devDependencies. Isso causa erros massivos de TypeScript em todos os arquivos JSX ao rodar `npm run lint`, mas o build Vite funciona normalmente (Vite tem resolução própria).

## Why This Matters
Ao editar qualquer componente React e rodar `npm run lint`, aparecem dezenas de erros sobre `JSX element implicitly has type 'any'` e similares — parece que você introduziu um problema, mas o problema é pré-existente na configuração do projeto.

## Recognition Pattern
- Stack: React + TypeScript + Vite neste projeto
- Erros: `Cannot find module 'react'`, `JSX element implicitly has type 'any'`
- Aparecem em TODOS os arquivos `.tsx` ao rodar `tsc --noEmit`
- O `npm run build` (Vite) funciona sem esses erros

## The Approach
Instalar os pacotes de tipos faltantes:
```bash
cd eventnexus-frontend
npm install --save-dev @types/react @types/react-dom
```

Após isso, `npm run lint` deve mostrar apenas erros reais, não os de JSX.

## Files
- `eventnexus-frontend/package.json` — onde os devDependencies ficam
