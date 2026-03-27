# FortiSIEM Adapter Server

FastAPI 어댑터 서버 (v2.0.0) — **FortiSOAR 커넥터**와 **FortiSIEM** 백엔드 데이터베이스를 연결합니다.
FortiSIEM HTTP REST API 대신 PostgreSQL·ClickHouse에 직접 접속하여 성능을 높입니다.

## 아키텍처

```
FortiSOAR Connector
        │
        ▼
FortiSIEM Adapter (FastAPI)   ← 이 서버
        │
        ├──► FortiSIEM PostgreSQL  (incidents, CMDB, watchlists, lookup tables)
        └──► FortiSIEM ClickHouse  (raw events, time-series queries)
```

### 레이어 구조

```
app/routers/        HTTP 엔드포인트 핸들러
app/services/       비즈니스 로직
app/repositories/   DB 쿼리 실행 (PostgreSQL / ClickHouse)
app/db/             커넥션 풀 관리 (asyncpg + clickhouse-connect)
app/core/           설정, 인증, 예외 처리
app/schemas/        Pydantic 요청/응답 모델
app/queue/          Redis/RQ 백그라운드 잡 큐
app/worker.py       RQ 워커 엔트리포인트
app/dependencies.py FastAPI DI 와이어링
```

### API 엔드포인트

| 경로 | 설명 |
|---|---|
| `GET /health` | DB 연결 상태 확인 |
| `POST /incidents` | 인시던트 목록 조회 |
| `POST /incidents/detail` | 인시던트 상세 조회 |
| `PUT /incidents` | 인시던트 상태/해결 업데이트 |
| `POST /incidents/comment` | 인시던트 코멘트 추가 |
| `GET /devices` | CMDB 디바이스 목록 |
| `GET /watchlists` | 워치리스트 CRUD |
| `GET /lookup-tables` | 룩업 테이블 CRUD |
| `GET /context/ip/{ip}` | IP 컨텍스트 조회 |
| `POST /phoenix/rest/query/eventQuery` | 이벤트 쿼리 제출 (queryId 반환) |
| `GET /phoenix/rest/query/progress/{queryId}` | 쿼리 진행률 (항상 100%) |
| `GET /phoenix/rest/query/events/{queryId}/{start}/{limit}` | 이벤트 결과 페이지 조회 |
| `GET /phoenix/rest/pub/incident` | 퍼블릭 인시던트 목록 |
| `GET /phoenix/rest/config/Domain` | 도메인 XML 반환 |

이벤트 쿼리는 FortiSIEM 7.4.2 OpenAPI 스펙의 3단계 비동기 패턴을 모방하지만, 내부적으로는 동기 실행 후 인메모리 캐시에 결과를 저장합니다.

---

## 실행 방법

### 1. 환경 설정

```bash
cp .env.example .env
# .env 파일을 열어 DB 접속 정보 입력
```

주요 환경 변수:

| 변수 | 기본값 | 설명 |
|---|---|---|
| `POSTGRES_HOST` | `localhost` | FortiSIEM PostgreSQL 호스트 |
| `POSTGRES_DB` | `phoenixdb` | FortiSIEM DB 이름 |
| `POSTGRES_USER` | `phoenix` | |
| `POSTGRES_PASSWORD` | _(필수)_ | |
| `CLICKHOUSE_HOST` | `localhost` | ClickHouse 호스트 |
| `CLICKHOUSE_PORT` | `8123` | ClickHouse HTTP 포트 |
| `REDIS_HOST` | `localhost` | 백그라운드 잡 큐용 Redis |
| `API_ORG` | `super` | 이 어댑터에 접속할 때 사용하는 org |
| `API_USERNAME` | `admin` | |
| `API_PASSWORD` | `changeme` | |

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 서버 실행

```bash
# 개발 서버 (자동 재시작)
uvicorn app.main:app --reload

# 특정 호스트/포트 지정
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. RQ 워커 실행 (백그라운드 잡 필요 시)

```bash
python app/worker.py
```

### 5. API 문서

서버 실행 후 브라우저에서 확인:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 인증

모든 엔드포인트는 FortiSIEM 형식의 HTTP Basic Auth를 사용합니다.

```
형식: org/username:password
예시: super/admin:changeme
      → Authorization: Basic c3VwZXIvYWRtaW46Y2hhbmdlbWU=
```

---

## 테스트

```bash
# 전체 테스트
pytest -v

# 특정 파일
pytest tests/test_incidents.py -v

# 특정 테스트
pytest tests/test_incidents.py::test_list_incidents -v
```

테스트는 `AsyncMock`으로 레포지토리를 모킹하므로 실제 DB 연결 없이 실행됩니다.


기능 구현 완료 목록.
1. Fortisoar Connector
- Ingest
- Fetch
- Get incident detail
- Get Incident List