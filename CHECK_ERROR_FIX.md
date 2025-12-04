# 오류 조치 확인 가이드

## ✅ 확인 방법

### 1단계: 서버 실행 확인
서버가 실행 중인지 확인합니다.

```bash
# PowerShell에서 실행
curl http://localhost:8000/docs
```

**예상 결과**: StatusCode 200이 반환되어야 합니다.

---

### 2단계: 브라우저에서 페이지 접속

1. 브라우저를 열고 다음 URL로 접속:
   ```
   http://localhost:8000/objects/overview
   ```

2. **예상 결과**:
   - 페이지가 정상적으로 로드됨
   - 필터, 검색창, 통계 정보가 표시됨
   - **중요**: 그래프 영역에 노드와 엣지가 표시되어야 함

---

### 3단계: 개발자 도구 콘솔 확인 (가장 중요!)

1. 브라우저에서 **F12** 키를 눌러 개발자 도구 열기
2. **Console** 탭 클릭
3. 페이지를 새로고침 (F5 또는 Ctrl+R)

**정상적인 경우 콘솔에 표시되는 메시지**:
```
DOM 로드 완료, 네트워크 초기화 시작...
네트워크 데이터 로딩 시작...
데이터 로드 완료: {nodes: Array(12), edges: Array(11), stats: {...}}
노드 수: 12 엣지 수: 11
네트워크 생성 시작...
네트워크 생성 완료
네트워크 안정화 완료
```

**오류가 있는 경우**:
- 빨간색 오류 메시지가 표시됨
- 예: `vis.js가 로드되지 않았습니다.`
- 예: `network-container를 찾을 수 없습니다.`
- 예: `HTTP error! status: 404`

---

### 4단계: API 엔드포인트 직접 테스트

PowerShell에서 실행:

```powershell
# 전체 맵 API 테스트
$response = curl http://localhost:8000/objects/overview/network
$json = $response.Content | ConvertFrom-Json
Write-Host "노드 수: $($json.nodes.Count)"
Write-Host "엣지 수: $($json.edges.Count)"
Write-Host "첫 번째 노드:"
$json.nodes[0] | ConvertTo-Json
Write-Host "첫 번째 엣지:"
$json.edges[0] | ConvertTo-Json
```

**예상 결과**:
- 노드 수: 12개 (또는 실제 데이터 수)
- 엣지 수: 11개 (또는 실제 데이터 수)
- 노드와 엣지 데이터가 JSON 형식으로 출력됨

---

### 5단계: 네트워크 그래프 시각적 확인

브라우저에서 `/objects/overview` 페이지에서:

1. **그래프 영역 확인**:
   - 노드(박스 형태)가 여러 개 표시되어야 함
   - 노드 간에 화살표(엣지)가 연결되어 있어야 함
   - 노드를 드래그할 수 있어야 함
   - 마우스 휠로 확대/축소가 가능해야 함

2. **기능 테스트**:
   - 노드 클릭 → 해당 오브젝트 상세 페이지로 이동
   - 노드 더블클릭 → 해당 노드로 포커스
   - "전체 보기" 버튼 클릭 → 그래프가 전체 보기로 조정됨
   - 필터 적용 → 그래프가 필터링됨

---

## 🔍 문제 해결 체크리스트

### 그래프가 보이지 않는 경우:

- [ ] 서버가 실행 중인가? (`curl http://localhost:8000/docs` 확인)
- [ ] 브라우저 콘솔에 오류가 있는가? (F12 → Console 탭 확인)
- [ ] API가 데이터를 반환하는가? (`/objects/overview/network` 테스트)
- [ ] vis.js가 로드되었는가? (콘솔에서 `typeof vis` 확인, `object`여야 함)
- [ ] 네트워크 컨테이너가 존재하는가? (콘솔에서 `document.getElementById('network-container')` 확인)

### 콘솔에서 직접 확인하는 방법:

브라우저 개발자 도구 콘솔에서 다음 명령어들을 실행:

```javascript
// 1. vis.js 로드 확인
console.log('vis.js:', typeof vis);

// 2. 네트워크 컨테이너 확인
console.log('container:', document.getElementById('network-container'));

// 3. API 데이터 확인
fetch('/objects/overview/network')
  .then(r => r.json())
  .then(data => {
    console.log('API 데이터:', data);
    console.log('노드 수:', data.nodes.length);
    console.log('엣지 수:', data.edges.length);
  });

// 4. 네트워크 객체 확인
console.log('network:', network);
```

---

## ✅ 정상 작동 확인 기준

다음 조건을 모두 만족하면 정상 작동하는 것입니다:

1. ✅ 페이지가 오류 없이 로드됨
2. ✅ 콘솔에 오류 메시지가 없음
3. ✅ 그래프 영역에 노드와 엣지가 표시됨
4. ✅ 노드를 드래그할 수 있음
5. ✅ 노드를 클릭하면 상세 페이지로 이동함
6. ✅ 필터 기능이 작동함

---

## 🚨 여전히 문제가 있는 경우

문제가 지속되면 다음 정보를 수집해주세요:

1. **브라우저 콘솔의 모든 오류 메시지** (스크린샷 또는 복사)
2. **네트워크 탭의 API 응답** (F12 → Network 탭 → `/objects/overview/network` 확인)
3. **사용 중인 브라우저 및 버전** (Chrome, Firefox, Edge 등)

이 정보를 바탕으로 추가 문제 해결을 진행할 수 있습니다.

