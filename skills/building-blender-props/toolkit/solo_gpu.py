"""Regla de Jorge (2026-10-13): PROHIBIDO renderizar u hornear con la CPU. La GPU es la unica responsable.

    import solo_gpu; solo_gpu.asegurar()        antes de cada `render.render` y de cada `object.bake`

Deja Cycles en GPU con OptiX, apaga el dispositivo CPU en las preferencias (encendido junto a las GPU, Cycles reparte
el render tambien a la CPU: el modo hibrido) y deja fuera la GTX 1080 Ti (Pascal, sin nucleos RT). Si no queda ninguna
GPU encendida LEVANTA: es preferible no renderizar a caer en la CPU sin avisar. Los motores que ya son de GPU (EEVEE,
Workbench) no se tocan, pero un horneado siempre es de Cycles y se fuerza igual.
"""
import bpy

FUERA = ("1080",)          # tarjetas sin nucleos RT


def asegurar(escena=None, horneado=False):
    sc = escena or bpy.context.scene
    if sc.render.engine != "CYCLES" and not horneado:
        return {"motor": sc.render.engine, "cycles": False}
    pr = bpy.context.preferences.addons["cycles"].preferences
    if pr.compute_device_type != "OPTIX":
        pr.compute_device_type = "OPTIX"
    pr.get_devices()
    usadas = []
    for d in pr.devices:
        d.use = d.type == "OPTIX" and not any(x in d.name for x in FUERA)
        if d.use:
            usadas.append(d.name)
    if not usadas:
        raise RuntimeError("solo_gpu: ninguna GPU disponible para Cycles. No se renderiza ni se hornea con la CPU.")
    sc.cycles.device = "GPU"
    # el denoiser tambien: OptiX corre en la tarjeta; OpenImageDenoise, solo si lo hace en GPU
    try:
        if sc.cycles.use_denoising and sc.cycles.denoiser == "OPENIMAGEDENOISE" and hasattr(sc.cycles, "denoising_use_gpu"):
            sc.cycles.denoising_use_gpu = True
    except Exception:
        pass
    return {"motor": "CYCLES", "dispositivo": sc.cycles.device, "gpus": usadas, "cpu": [d.name for d in pr.devices if d.type == "CPU" and d.use]}
