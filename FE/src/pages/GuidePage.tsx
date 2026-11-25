import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { AppLayout } from '../components/AppLayout'

/** 이용 안내 + 데이터 출처·이용조건 (SRS 2.4 제약사항) + 개인정보 처리 안내 */
export function GuidePage() {
  const { isAuthenticated } = useAuth()
  return (
    <AppLayout guest={!isAuthenticated}>
      <div className="guide">
        <header className="page-head">
          <div>
            <h1 className="page-head__title">이용 안내</h1>
            <p className="page-head__sub">부산이음은 부산 청년을 위한 교육·취업 AI 안내 서비스예요.</p>
          </div>
        </header>

        <section className="card">
          <h2 className="card__title">이렇게 사용해요</h2>
          <ol className="guide__list">
            <li>
              <strong>텍스트로 물어보기</strong> — 희망 직무, 경력, 관심 분야를 적으면 부산 지역 교육·채용 정보를 각각 2건씩 추천해요.
              “교육만 5개”처럼 개수나 종류를 정할 수도 있어요.
            </li>
            <li>
              <strong>이미지로 물어보기</strong> — 채용 공고나 교육 안내 이미지(JPG·PNG, 5MB 이하)를 올리면 지원 자격, 신청 방법 등 핵심 내용을 정리해요.
            </li>
            <li>
              <strong>내역 다시 보기</strong> — 질의응답 내역에서 이전 대화를 보고, Markdown 파일로 내려받을 수 있어요.
            </li>
          </ol>
          {!isAuthenticated && (
            <Link to="/signup" className="btn btn--primary">
              무료로 시작하기
            </Link>
          )}
        </section>

        <section className="card">
          <h2 className="card__title">데이터 출처와 이용 조건</h2>
          <ul className="guide__list">
            <li>
              교육과정: 고용노동부 <a href="https://www.work24.go.kr/cm/e/a/0110/selectOpenApiIntro.do" target="_blank" rel="noopener noreferrer">고용24 오픈API</a> (국민내일배움카드 훈련과정)
            </li>
            <li>
              채용정보: <a href="https://www.data.go.kr/data/15125273/openapi.do" target="_blank" rel="noopener noreferrer">공공데이터포털 · 청년 일자리 지원 서비스</a>
            </li>
            <li>추천 결과는 공공데이터를 바탕으로 AI가 정리한 참고 정보이며, 실제 신청·지원은 각 원문 페이지에서 진행해 주세요.</li>
          </ul>
        </section>

        <section className="card" id="privacy">
          <h2 className="card__title">개인정보 처리 안내</h2>
          <ul className="guide__list">
            <li>수집 항목은 이메일, 이름, 암호화된 비밀번호뿐이에요.</li>
            <li>질문에 포함된 주민등록번호·전화번호·이메일 등은 가려서 처리하고 저장해요.</li>
            <li>업로드한 이미지 원본은 저장하지 않고, 분석된 텍스트 결과만 대화 내역에 남겨요.</li>
          </ul>
        </section>
      </div>
    </AppLayout>
  )
}
