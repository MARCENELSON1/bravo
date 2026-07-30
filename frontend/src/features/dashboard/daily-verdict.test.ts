import { describe, expect, it } from "vitest"

import { dailyVerdict } from "@/features/dashboard/daily-verdict"
import { tomorrowTask } from "@/features/dashboard/tomorrow-task"
import type { FinanceDiagnosticDTO } from "@/api/types-operations"

describe("dailyVerdict", () => {
  it("net negativo → bad", () => {
    expect(dailyVerdict(-5000, null).tone).toBe("bad")
  })

  it("net positivo sin ayer → good, sin comparativo", () => {
    const v = dailyVerdict(1000, null)
    expect(v.tone).toBe("good")
    expect(v.message).not.toContain("%")
  })

  it("mejor que ayer → good con % más", () => {
    const v = dailyVerdict(2000, 100)
    expect(v.tone).toBe("good")
    expect(v.message).toContain("100% más")
  })

  it("peor que ayer pero en ganancia → ok con % menos", () => {
    const v = dailyVerdict(800, -20)
    expect(v.tone).toBe("ok")
    expect(v.message).toContain("20% menos")
  })
})

describe("tomorrowTask", () => {
  const diag = (severity: string, action: string): FinanceDiagnosticDTO => ({
    code: severity,
    severity,
    bucket: "today",
    title: "t",
    body: "b",
    action,
  })

  it("devuelve la acción del diagnóstico más severo", () => {
    const task = tomorrowTask([diag("warn", "revisá turnos"), diag("alert", "renegociá proveedor")])
    expect(task).toBe("renegociá proveedor")
  })

  it("ignora los healthy y devuelve null si no hay accionables", () => {
    expect(tomorrowTask([diag("healthy", "seguí así")])).toBeNull()
    expect(tomorrowTask([])).toBeNull()
  })
})
