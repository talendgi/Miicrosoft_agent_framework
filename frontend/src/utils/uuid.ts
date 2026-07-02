export const v4 = () =>
  crypto.randomUUID?.() ??
  `id_${Math.random().toString(16).slice(2)}_${Date.now().toString(16)}`;
