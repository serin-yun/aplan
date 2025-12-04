# 일반 사용자 가시성 개선 방안

## 🎨 시각적 개선 방안

### 1. 노드 크기 및 가독성 개선

**현재 상태:**
- 노드 크기가 고정되어 있음
- 폰트 크기 14px (작을 수 있음)
- 레이블이 2줄로 표시되어 읽기 어려움

**개선 방안:**

#### A. 연결도에 따른 노드 크기 조절
```javascript
// 노드 생성 시 연결도(degree) 계산하여 크기 설정
nodes: {
    size: function(node) {
        // 연결된 엣지 수에 따라 크기 조절
        const degree = edges.get({filter: (e) => e.from === node.id || e.to === node.id}).length;
        return Math.max(20, Math.min(50, 20 + degree * 3)); // 20~50px 범위
    },
    font: {
        size: 16,  // 14 → 16으로 증가
        bold: true  // 굵게 표시
    }
}
```

#### B. 레이블 표시 개선
```javascript
// 레이블을 더 읽기 쉽게 표시
label: `${obj.system_type}\n${obj.name}` 
// → 
label: `${obj.name}\n[${obj.system_type}]`  // 이름을 먼저, 시스템 타입을 작게
// 또는
label: obj.name,  // 이름만 표시하고 시스템 타입은 색상으로 구분
```

#### C. 노드 최소/최대 크기 설정
```javascript
nodes: {
    size: {
        min: 30,  // 최소 크기
        max: 80   // 최대 크기
    }
}
```

---

### 2. 색상 및 시각적 구분 강화

**현재 상태:**
- 시스템 타입별 색상은 있지만 대비가 약할 수 있음
- 엣지 색상이 회색으로 단조로움

**개선 방안:**

#### A. 시스템 타입별 색상 대비 강화
```python
# app/routers/objects.py의 system_colors 개선
system_colors = {
    "SAP": {
        "background": "#0f7b0f",      # 더 밝은 녹색
        "border": "#0a5a0a",
        "highlight": {"background": "#12a012", "border": "#0a5a0a"}
    },
    # 각 시스템 타입의 색상을 더 선명하고 구분되게
}
```

#### B. 엣지 색상을 시스템 타입에 맞게
```javascript
// 엣지 색상을 출발 노드의 시스템 타입에 맞춤
edges: {
    color: {
        color: function(edge) {
            const fromNode = nodes.get(edge.from);
            return getSystemColor(fromNode.group);  // 시스템 타입별 색상
        },
        highlight: '#ff0000'
    },
    width: function(edge) {
        // 중요도에 따라 두께 조절
        return 2;  // 또는 중요도 기반으로 1~4px
    }
}
```

#### C. 노드 테두리 두께 증가
```javascript
nodes: {
    borderWidth: 3,  // 2 → 3으로 증가하여 더 명확하게
    borderWidthSelected: 5  // 선택 시 더 두껍게
}
```

---

### 3. 레이아웃 및 배치 개선

**현재 상태:**
- 자동 레이아웃이지만 노드가 겹칠 수 있음
- 계층 구조가 명확하지 않음

**개선 방안:**

#### A. 계층적 레이아웃 적용
```javascript
layout: {
    hierarchical: {
        enabled: true,
        direction: 'LR',  // Left to Right (좌→우)
        sortMethod: 'directed',  // 방향성 기반 정렬
        levelSeparation: 150,  // 레벨 간 거리
        nodeSpacing: 200,  // 노드 간 거리
        treeSpacing: 200,  // 트리 간 거리
    }
}
```

#### B. 레이어별 그룹화
```javascript
// 레이어(Layer)별로 수평선으로 구분
// 예: Legacy → API → Staging → Out 순서로 배치
```

#### C. 노드 간 최소 거리 보장
```javascript
physics: {
    barnesHut: {
        springLength: 150,  // 95 → 150으로 증가하여 더 넓게 배치
        springConstant: 0.03,  // 약간 감소하여 더 부드럽게
    }
}
```

---

### 4. 인터랙션 및 사용성 개선

**현재 상태:**
- 기본적인 드래그, 확대/축소 기능만 있음

**개선 방안:**

#### A. 호버 시 상세 정보 표시
```javascript
network.on('hoverNode', function(params) {
    // 노드에 마우스를 올리면 상세 정보 툴팁 표시
    // object_key, description, module 등 표시
});
```

#### B. 선택된 노드의 연결 강조
```javascript
network.on('selectNode', function(params) {
    // 선택된 노드와 연결된 노드/엣지만 강조 표시
    // 나머지는 반투명 처리
});
```

#### C. 미니맵 추가
```javascript
// 전체 맵의 축소된 미니맵을 우측 하단에 표시
// 현재 보이는 영역 표시 및 클릭으로 이동
```

#### D. 줌 컨트롤 추가
```javascript
// 줌 인/아웃 버튼 추가
// 줌 레벨 표시 (예: 100%, 150% 등)
```

---

### 5. 정보 표시 개선

**현재 상태:**
- 노드에 시스템 타입과 이름만 표시

**개선 방안:**

#### A. 노드에 아이콘 추가
```javascript
nodes: {
    shape: 'icon',  // 또는 'image'
    icon: {
        face: 'FontAwesome',  // FontAwesome 아이콘 사용
        code: '\uf1c0',  // 시스템 타입별 다른 아이콘
        size: 30,
        color: '#ffffff'
    }
}
```

#### B. 노드에 상태 표시
```javascript
// ACTIVE/DRAFT/DEPRECATED 상태를 노드 모서리에 배지로 표시
// 또는 노드 색상으로 구분
```

#### C. 연결 수 표시
```javascript
// 노드에 연결된 엣지 수를 숫자로 표시
label: `${obj.name}\n(${connectionCount})`
```

---

### 6. 필터링 및 검색 개선

**현재 상태:**
- 기본적인 필터만 있음

**개선 방안:**

#### A. 필터 적용 시 애니메이션
```javascript
// 필터 적용 시 노드가 부드럽게 나타나거나 사라지도록
network.setOptions({
    nodes: {
        opacity: 0.3  // 필터링되지 않은 노드는 반투명
    }
});
```

#### B. 검색 결과 하이라이트 강화
```javascript
// 검색된 노드만 강조하고 나머지는 반투명 처리
// 검색된 노드로 자동 줌 인
```

#### C. 범례(Legend) 추가
```javascript
// 시스템 타입별 색상 범례를 그래프 옆에 표시
// 클릭하면 해당 시스템 타입만 필터링
```

---

### 7. 성능 및 대용량 데이터 대응

**개선 방안:**

#### A. 노드 수에 따른 자동 조정
```javascript
// 노드가 많을 경우 (예: 100개 이상)
// - 레이블 표시 간소화
// - 엣지 두께 감소
// - 물리 엔진 파라미터 조정
```

#### B. 로딩 인디케이터
```javascript
// 데이터 로딩 중 스피너 표시
// "데이터 로딩 중... (12/12)" 같은 진행률 표시
```

---

### 8. 접근성 개선

**개선 방안:**

#### A. 키보드 단축키
```javascript
// 방향키로 네트워크 이동
// +/- 키로 줌 인/아웃
// Enter로 선택된 노드 상세 페이지 이동
```

#### B. 색상 대비 개선
```javascript
// WCAG 접근성 기준에 맞는 색상 대비 비율 확보
// 색맹 사용자도 구분 가능하도록 패턴/모양 추가
```

---

## 📊 우선순위별 개선 방안

### 🔴 높은 우선순위 (즉시 적용 권장)

1. **노드 크기 조절** - 연결도에 따라 크기 변경
2. **폰트 크기 증가** - 14px → 16px
3. **노드 테두리 두께 증가** - 2px → 3px
4. **엣지 색상 개선** - 회색 → 시스템 타입별 색상
5. **호버 시 상세 정보** - 툴팁 표시

### 🟡 중간 우선순위 (단기 개선)

1. **계층적 레이아웃** - 레이어별 정렬
2. **선택 노드 강조** - 연결된 노드만 표시
3. **범례 추가** - 시스템 타입별 색상 범례
4. **검색 하이라이트 강화** - 나머지 노드 반투명 처리

### 🟢 낮은 우선순위 (장기 개선)

1. **미니맵 추가**
2. **아이콘 추가**
3. **키보드 단축키**
4. **애니메이션 효과**

---

## 💡 구현 시 고려사항

1. **성능**: 노드가 많을 경우 (100개 이상) 성능 저하 가능
2. **사용자 피드백**: 개선 후 실제 사용자 테스트 권장
3. **점진적 개선**: 한 번에 모든 것을 적용하지 말고 단계적으로
4. **설정 옵션**: 사용자가 일부 옵션을 켜고 끌 수 있도록 설정 메뉴 추가 고려

---

## 🎯 가장 효과적인 개선 조합

**빠른 효과를 위한 최소 변경:**

1. 노드 크기: 연결도 기반 (20~50px)
2. 폰트 크기: 16px, 굵게
3. 테두리: 3px
4. 엣지 색상: 시스템 타입별
5. 호버 툴팁: 상세 정보 표시

이 5가지만 적용해도 가시성이 크게 향상됩니다.

