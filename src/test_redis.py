import redis

def test_redis_connection():
    try:
        # Conecta ao Redis
        r = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        
        # Testa a conexão
        r.set('test_key', 'Conexão com Redis funcionando!')
        result = r.get('test_key')
        print(f"Teste de conexão: {result}")
        
        # Limpa o teste
        r.delete('test_key')
        return True
        
    except redis.ConnectionError as e:
        print(f"Erro de conexão com Redis: {str(e)}")
        return False
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return False

if __name__ == '__main__':
    test_redis_connection()
