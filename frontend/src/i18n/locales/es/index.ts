// Barrel del idioma español. Un namespace por feature (archivo aparte) para que
// los diccionarios sigan siendo navegables a medida que crece la app. Español es
// el idioma base (paridad): las nuevas pantallas se migran a `t()` de a poco.
import { auth } from "./auth"
import { common } from "./common"
import { dashboard } from "./dashboard"
import { errors } from "./errors"
import { identity } from "./identity"
import { login } from "./login"
import { shell } from "./shell"

export const es = { common, login, auth, identity, errors, shell, dashboard } as const
