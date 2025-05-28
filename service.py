import logging
import json
import time
from kafka_tools import KafkaMessageConsumer, KafkaMessageProducer
from config import KAFKA_TOPICS, KAFKA_CONSUMER_GROUPS, ACTOR_GRACE_PERIOD, NFS_MOUNT_POINT, NFS_IP
import pipeline
import nfs_tools
import uuid

NAME = "SERVICE_VOICEFIXER"

# Настроим логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем топик и группу
topic = KAFKA_TOPICS.get("audio_raw")
group = KAFKA_CONSUMER_GROUPS.get("audio_voicefixers_group")
producer_topic = KAFKA_TOPICS.get("audio_buffed")

# Инициализируем Kafka consumer
consumer = KafkaMessageConsumer(topic=topic, group=group)

# Инициализируем Kafka producer
producer = KafkaMessageProducer(producer_topic)
def serve(key, value):
    logger.info(f"{NAME}| ✴️ Got kafka message with key: {key}!")
    """Обработка сообщений"""
    try:
        data = json.loads(value)
        file_path = data.get("filePath")
        file_name = data.get("originalName")

        logger.info(f"Calling pipeline on {file_name}")

        pipeline_uuid = str(uuid.uuid4())

        logger.info(f"Assigned nfs uuid: {pipeline_uuid}")

        pipeline_error_flag, final_path, vocals_path = pipeline.run(input_path=file_path, nfs_dir=file_path, uuid=pipeline_uuid)

        if pipeline_error_flag is False:
            logger.info(f"Pipeline {pipeline_uuid} ended successfully!")
        else:
            logger.error(f"Pipeline {pipeline_uuid} encountered internal errors!")

        message = json.dumps(
            {
                "uuid": pipeline_uuid,
                "final_path": final_path,
                "vocals_path": vocals_path,
            }
        )

        logger.info(f"⏩ Producer is sending message to {producer_topic}")
        producer.send_message(key=key, value=message)

        logger.info(f"🚀 Work cycle on {pipeline_uuid} done!")

    except json.JSONDecodeError as e:
        logger.error(f"{NAME} | ❌ JSON decoding error: {e}")
    except Exception as e:
        logger.error(f"{NAME} | ❌ Error processing message: {e}")


if __name__ == "__main__":
    logger.info(f"{NAME} | ⏳ Sleeping for {ACTOR_GRACE_PERIOD} seconds...")
    nfs_tools.mount_nfs_in_self(nfs_server_ip=NFS_IP, nfs_path=NFS_MOUNT_POINT, mount_point=NFS_MOUNT_POINT)
    time.sleep(ACTOR_GRACE_PERIOD)
    logger.info("Running external health-checks...")
    if not nfs_tools.check_nfs_server(NFS_MOUNT_POINT):
        logger.warning("NFS server is not available! Crucial functionality likely to be unavailable.")
    else:
        logger.info("NFS server is available!")
    try:
        logger.info(f"{NAME} | 🔄 Starting Kafka consumer...")
        consumer.consume_messages(serve)
    except Exception as e:
        logger.error(f"{NAME} | ❌ Error in Kafka consumer: {e}")
    finally:
        logger.info(f"{NAME} | 🛑 Stopping Kafka consumer...")
        consumer.close()  # Закрываем consumer корректно
        producer.flush()

