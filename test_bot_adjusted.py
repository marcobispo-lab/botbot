import os
import logging
import requests
import schedule
import time
import random
from datetime import datetime
from typing import Dict
import json

class TelegramBot:
    def __init__(self, config_file: str = 'config.json'):
        """Inicializar bot con configuración"""
        self.config = self._load_config(config_file)
        self.setup_logging()
        
        self.stats = {
            'green_count': 0,
            'red_count': 0,
            'profit_1_5': 0,
            'profit_2_0': 0,
            'last_signal_time': None,
            'signals_sent_today': 0
        }
        
        self.win_rate = self.config['win_rate']
        self.min_interval = self.config['min_interval_minutes']
        
    def _load_config(self, config_file: str) -> Dict:
        """Cargar configuración desde archivo JSON"""
        default_config = {
            'bot_token': '7748559341:AAFB4mo2oM1UN-CHlxtu9XNxtkJI1QwrMYY',
            'channel_id': '-1002289589941',
            'win_rate': 0.85,  # Ajustado para permitir algumas perdas
            'min_interval_minutes': 5,
            'start_hour': 11,  # Novo horário de início
            'end_hour': 23,    # Novo horário de término
            'signals_per_hour': 3,  # Reduzido para 3 sinais por hora
            'log_file': 'telegram_bot.log',
            'multiplier_range': {
                'min': 2.3,
                'max': 5.0
            }
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return {**default_config, **json.load(f)}
        except Exception as e:
            logging.warning(f"Error al cargar archivo de configuración: {e}. Usando valores predeterminados.")
        return default_config

    def setup_logging(self):
        """Configurar registro de eventos"""
        logging.basicConfig(
            filename=self.config['log_file'],
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def send_message(self, message: str) -> bool:
        """Enviar mensaje al canal de Telegram"""
        url = f'https://api.telegram.org/bot{self.config["bot_token"]}/sendMessage'
        data = {
            'chat_id': self.config['channel_id'],
            'text': message,
            'parse_mode': 'HTML'
        }
        
        for attempt in range(3):
            try:
                response = requests.post(url, data=data, timeout=10)
                if response.status_code == 200:
                    logging.info(f"Mensaje enviado con éxito: {message[:50]}...")
                    return True
                else:
                    logging.error(f"Error al enviar mensaje: {response.status_code} - {response.text}")
            except requests.RequestException as e:
                logging.error(f"Error en la solicitud: {e}")
                time.sleep(2 ** attempt)
        return False

    def generate_multiplier(self) -> float:
        """Generar multiplicador aleatorio"""
        min_mult = self.config['multiplier_range']['min']
        max_mult = self.config['multiplier_range']['max']
        return round(random.uniform(min_mult, max_mult), 2)

    def simulate_result(self) -> bool:
        """Simular resultado de señal"""
        return random.random() < self.win_rate

    def format_profit_message(self, is_win: bool, multiplier: float) -> str:
        """Formatear mensaje de ganancias"""
        base_profit = 50
        if is_win:
            profit_1_5 = base_profit
            profit_2_0 = base_profit * 1.5
            self.stats['profit_1_5'] += profit_1_5
            self.stats['profit_2_0'] += profit_2_0
            return f"💰 Ganancias estimadas:\n1.5x ➜ +${profit_1_5}\n2.0x ➜ +${profit_2_0}"
        return "📊 ¡Mantén tu gestión! Próxima señal en breve."

    def send_signal(self):
        """Enviar secuencia completa de señal"""
        current_time = datetime.now()
        
        if (self.stats['last_signal_time'] and 
            (current_time - self.stats['last_signal_time']).total_seconds() < self.min_interval * 60):
            return

        # Mensaje de análisis
        self.send_message(
            "⚙️ <b>ANÁLISIS EN CURSO</b>\n"
            "🔍 La IA está procesando patrones de los últimos 60 minutos...\n"
            "⏳ Preparando señal..."
        )
        time.sleep(random.randint(30, 90))

        # Generar y enviar señal
        multiplier = self.generate_multiplier()
        signal_message = (
            "🎯 <b>¡SEÑAL CONFIRMADA!</b>\n\n"
            "⚡️ Entrar ahora\n"
            f"⛔️ Salir Antes: {multiplier}x\n\n"
            "🔒 Protección recomendada: 1.5x HASTA 2.3X\n\n"
            "🎮 Gestión sugerida:\n"
            "• Entrada mínima: $5\n"
            "• No martingala\n"
            "• Respeta las señales\n\n"
            " 👇 Enlace para acceder al juego 👇\n"
            "https://1wzvro.top/v3/reg-form-aviator?p=ekvc"
        )
        self.send_message(signal_message)
        
        # Simular y enviar resultado
        time.sleep(random.randint(60, 180))
        is_win = self.simulate_result()
        
        if is_win:
            self.stats['green_count'] += 1
            result_message = (
                "✅ <b>¡GANAMOS!</b>\n\n"
                "🎯 Señal cerrada con éxito\n"
            )
        else:
            self.stats['red_count'] += 1
            result_message = (
                "❌ <b>PERDIMOS</b>\n\n"
                "💪 ¡Mantén la calma y sigue la estrategia!\n"
            )
        
        result_message += self.format_profit_message(is_win, multiplier)
        self.send_message(result_message)
        
        self.stats['last_signal_time'] = current_time
        self.stats['signals_sent_today'] += 1
        
        logging.info(f"Señal completada - Resultado: {'GANÓ' if is_win else 'PERDIÓ'}, "
                    f"Multiplicador: {multiplier}, Hora: {current_time}")

    def send_daily_summary(self):
        """Enviar resumen diario y reiniciar estadísticas"""
        total_signals = max(self.stats['signals_sent_today'], 1)
        win_rate = (self.stats['green_count'] / total_signals) * 100
        
        summary_message = (
            "📊 <b>RESUMEN DEL DÍA</b>\n\n"
            f"✅ Victorias: {self.stats['green_count']}\n"
            f"❌ Derrotas: {self.stats['red_count']}\n"
            f"📈 Tasa de acierto: {win_rate:.1f}%\n\n"
            f"💰 Ganancias acumuladas (1.5x): ${self.stats['profit_1_5']}\n"
            f"💰 Ganancias acumuladas (2.0x): ${self.stats['profit_2_0']}\n\n"
            "⭐️ Resumen de resultados:\n"
            f"• Señales totales: {total_signals}\n"
            f"• Promedio de ganancia: ${(self.stats['profit_1_5']/total_signals):.2f}\n\n"
            "🌟 ¡Nos vemos mañana con más señales!\n"
            "📱 Activa las notificaciones para no perderte ninguna señal"
        )
        self.send_message(summary_message)
        
        # Enviar mensaje de pausa noturna
        night_message = (
            "🌙 <b>ANÁLISIS NOCTURNO</b>\n\n"
            "📊 Después de un análisis exhaustivo del historial de resultados del juego, "
            "Identificamos que las próximas horas presentan patrones muy impredecibles.\n\n"
            "🔄 Nuestra IA continuará monitoreando y tan pronto como identifique más patrones "
            "asertivos, enviaremos señales nuevamente.\n\n"
            "⏰ Estén atentos a las notificaciones!"
        )
        self.send_message(night_message)
        
        # Reiniciar estadísticas
        self.stats = {key: 0 for key in self.stats}
        self.stats['last_signal_time'] = None
        
        logging.info("Resumen diario enviado y estadísticas reiniciadas")

    def schedule_signals(self):
        """Programar señales para el día"""
        # Programar resumen diario
        schedule.every().day.at("23:59").do(self.send_daily_summary)
        
        # Programar señales durante el día com horários completamente aleatórios
        for hour in range(self.config['start_hour'], self.config['end_hour'] + 1):
            # Dividir a hora em três partes para distribuir melhor os sinais
            for _ in range(self.config['signals_per_hour']):
                minute = random.randint(0, 59)
                schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.send_signal)

    def run(self):
        """Ejecutar bot principal"""
        self.schedule_signals()
        logging.info("Bot iniciado y señales programadas")
        
        # Mensaje de inicio
        welcome_message = (
            "🎯 <b>¡BOT DE SEÑALES ACTIVADO!</b>\n\n"
            "📊 Información importante:\n\n"
            "🚨 INTELIGENCIA ARTIFICIAL ESTÁ IDENTIFICANDO PATRONES FAVORABLES PARA EL REINICIO DE OPERACIONES\n\n"
            "⚠️ Recordatorios:\n"
            "• Gestión sugerida: $5 - $100\n"
            "• Usar gestión responsable\n"
            "• No hacer martingala\n"
            "• Respetar las señales\n\n"
            "🔔 Activa las notificaciones para recibir todas las señales"
        )
        self.send_message(welcome_message)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Bot detenido por el usuario")
        except Exception as e:
            logging.error(f"Error en el bot: {e}")
            raise

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()