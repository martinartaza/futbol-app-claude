# E01-T3 - Contratos compartidos: notas

Ticket: [`requirements/0003-shared-contracts.md`](../../requirements/0003-shared-contracts.md), tag
`v0.1.3`.

## Alternativas y elección

- **Un requerimiento o dos.** El esqueleto web se partió en dos: este (tooling del
  workspace, que también van a usar Android e iOS) y el 0004 (la app web). Así cada uno
  tiene sus tests en su proyecto (Python del workspace, TypeScript de web).
- **Paleta.** Sale del logo: rojo `#D63B32`, azul `#3C8DDB` y verde cancha `#5FA83A`.
  Medido el contraste WCAG: el azul con texto blanco da 3.49 y el verde 2.94, por debajo
  de AA (4.5). Se eligió usar los colores exactos del logo solo en gráficos (radar,
  flechas, cancha; ahí alcanza 3:1) y tonos ajustados donde hay texto encima (azul
  `#1F6FBF`, verde `#2E7D32`).
- **Tipografía.** La del logo se parece a Comic Sans y al usuario le pareció muy simple;
  se eligió Inter (legible en pantallas chicas, buenos números para puntajes). Las
  letras del logo quedan como imagen.
- **Formato de modos.** El formato W3C de Design Tokens no trae temas; cada token lleva
  sus dos valores en `$extensions.modes` (`white`, `dark`) y el fondo nombra su texto en
  `$extensions.pair`, que es lo que el script controla con contraste.

## Instalación y configuración

- `scripts/sync_contracts.py` usa solo la biblioteca estándar de Python; no hay nada que
  instalar. Se corre desde la raíz: `python3 scripts/sync_contracts.py`, y en CI
  `--check`.
- Genera, si existe la carpeta `web/`: `web/src/generated/tokens.css` (blanco en
  `:root`, oscuro con `prefers-color-scheme: dark`), `tokens.ts` (tipo `TokenName` y
  `token()`) y la copia del schema GraphQL del backend.

## Problemas y soluciones

- **Un caso de test mal elegido**: el primer color para probar contraste insuficiente
  (`#3C8DDB` sobre `#121614`) en realidad pasa (5.24). Se calculó antes de correr y se
  cambió por `#C62F27` (3.33), todavía en rojo.
- **El guard de la shell** frena comandos o heredocs que mencionan el archivo de schema
  generado aunque solo sea texto; los cambios de documentos se hicieron con Edit.

## Otras notas

- Los errores se reportan todos juntos y en su origen: si un token no tiene valor, los
  que lo referencian no repiten el error.
- `button` es un componente compartido por la pantalla de actualización y el error de
  conexión, en lugar de un grupo `update` propio.
- El usuario corrió el script, revisó `base.json` y los archivos generados, y dio el
  ticket por terminado el 2026-11-15.
