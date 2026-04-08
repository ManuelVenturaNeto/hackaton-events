# Vite + TypeScript: `ImportMeta.env` Type Error

## The Insight
Projetos Vite com TypeScript podem ter o erro `Property 'env' does not exist on type 'ImportMeta'` em `src/api.ts` ou qualquer arquivo que use `import.meta.env`. Isso acontece porque os tipos do Vite (`vite/client`) não estão incluídos no `tsconfig.json`.

## Why This Matters
O erro bloqueia `npm run lint` com falso positivo — o código funciona em runtime mas o TypeScript não reconhece `import.meta.env`. É fácil confundir com um erro real introduzido por uma mudança recente.

## Recognition Pattern
- Stack: Vite + TypeScript
- Erro: `error TS2339: Property 'env' does not exist on type 'ImportMeta'`
- Arquivo afetado: qualquer arquivo que usa `import.meta.env.VITE_*`
- O erro existe desde o início do projeto (não foi introduzido por mudança recente)

## The Approach
Adicionar `"vite/client"` em `compilerOptions.types` no `tsconfig.json`:

```json
{
  "compilerOptions": {
    "types": ["vite/client"]
  }
}
```

Ou alternativamente criar/atualizar `src/vite-env.d.ts`:
```typescript
/// <reference types="vite/client" />
```

## Files
- `eventnexus-frontend/tsconfig.json` — onde adicionar o fix
- `eventnexus-frontend/src/api.ts` — arquivo com o erro
