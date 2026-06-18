from datetime import datetime, timedelta

def gerar_horarios_do_dia():
    
    horarios = []
    
    horario_atual = datetime.strptime(
        "08:00",
        "%H:%M"
    )
    
    horario_final = datetime.strptime(
        "18:00",
        "%H:%M"
    )
    
    while horario_atual <= horario_final:
        
        horarios.append(
            horario_atual.strftime("%H:%M")
        )
        
        horario_atual += timedelta(minutes=30)
        
    return horarios