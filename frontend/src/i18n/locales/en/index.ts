// English (US) barrel. Same namespaces as `es` — one file per feature so the
// dictionaries stay navigable as the app grows.
import { auth } from "./auth"
import { common } from "./common"
import { dashboard } from "./dashboard"
import { errors } from "./errors"
import { identity } from "./identity"
import { login } from "./login"
import { shell } from "./shell"

export const en = { common, login, auth, identity, errors, shell, dashboard } as const
