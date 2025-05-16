docker-compose -f zk-single-kafka.yml up -d
docker-compose -f zk-single-kafka.yml ps
kafka-topics --create --topic music_events --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
kafka-topics --create --topic farm_predictions --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
spark-submit --packages org.postgresql:postgresql:42.7.3,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5 farm_predictions.py
