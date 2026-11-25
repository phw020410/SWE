import { Link } from 'react-router-dom'
import { AppLayout } from '../components/AppLayout'
import { Composer } from '../components/Composer'
import { IconArrowRight, IconBriefcase, IconExternal, IconGraduation, IconLightbulb, IconLock, IconShield, IconSparkle } from '../components/Icons'
import { LogoMark } from '../components/Logo'

/** 로그인 전 첫 화면: 서비스 미리보기 (SRS 목업 preview) */
export function LandingPage() {
  return (
    <AppLayout guest>
      <div className="landing">
        <p className="eyebrow">
          <IconSparkle size={15} /> 부산의 교육과 취업, 대화로 가볍게
        </p>
        <h1>어디서 시작할지 막막할 때, 부산이음</h1>
        <p className="lead">관심 직무와 희망 지역을 알려주세요. 나에게 맞는 배움과 일의 방향을 함께 찾아드려요.</p>

        <div className="landing__grid">
          <section className="card preview">
            <div className="preview__head">
              <h2 className="card__title">이렇게 대화해 보세요</h2>
              <span className="badge badge--teal">대화 미리보기</span>
            </div>
            <div className="msg msg--user">
              <div className="bubble">부산에서 데이터 분석 일을 시작하고 싶어요. 비전공자도 들을 수 있는 교육이 있을까요?</div>
              <span className="msg__time">나의 질문 예시</span>
            </div>
            <div className="msg msg--assistant">
              <div className="msg__author">
                <LogoMark size={26} />
                <strong>부산이음 AI</strong>
                <span className="badge badge--teal">커리어 길잡이</span>
              </div>
              <p className="msg__text">물론이에요! 처음 시작한다면 기초를 배우고 작은 프로젝트를 완성하는 과정부터 추천해요. 부산에서 이런 경로를 살펴볼 수 있어요.</p>
              <div className="preview__rows">
                <div className="preview__row">
                  <IconGraduation />
                  <div>
                    <strong>배움부터 시작하기</strong>
                    <span>고용24 국민내일배움카드 훈련과정에서 찾아요</span>
                  </div>
                  <IconExternal size={16} />
                </div>
                <div className="preview__row">
                  <IconBriefcase />
                  <div>
                    <strong>배운 내용을 일로 연결하기</strong>
                    <span>청년 일자리 지원 서비스의 부산 채용정보와 함께 봐요</span>
                  </div>
                  <IconExternal size={16} />
                </div>
              </div>
            </div>
            <div className="preview__cta">
              <p>
                <IconLock size={16} /> <strong>로그인 후 사용해보세요</strong>
              </p>
              <span>나만의 추천을 받고, 대화 내역도 이어서 확인할 수 있어요.</span>
              <div className="preview__buttons">
                <Link to="/login" className="btn btn--primary">
                  <IconArrowRight size={16} /> 로그인하고 질문하기
                </Link>
                <Link to="/signup" className="btn btn--outline">
                  회원가입
                </Link>
              </div>
            </div>
          </section>

          <aside className="landing__side">
            <section className="card steps">
              <h2 className="card__title">가볍게 말하면, 함께 찾아요</h2>
              <ol>
                <li>
                  <strong>나의 관심사 이야기하기</strong>
                  <span>직무, 경험, 희망 지역을 알려주세요.</span>
                </li>
                <li>
                  <strong>맞춤 추천 살펴보기</strong>
                  <span>교육과 일자리 정보를 함께 정리해요.</span>
                </li>
                <li>
                  <strong>대화를 이어가며 구체화하기</strong>
                  <span>조건을 더하면 방향이 더 또렷해져요.</span>
                </li>
              </ol>
            </section>
            <section className="card card--mint tips">
              <IconLightbulb />
              <h2 className="card__title">이런 질문도 좋아요</h2>
              <ul>
                <li>“해운대구에서 일하고 싶어요.”</li>
                <li>“6개월 안에 배울 수 있는 교육은?”</li>
                <li>“신입도 가능한 직무를 알려줘.”</li>
              </ul>
            </section>
            <p className="landing__note">
              <IconShield size={14} /> 교육·채용 정보는 고용24와 청년 일자리 지원 서비스의 공공데이터를 이용해요.
            </p>
          </aside>
        </div>

        <div className="landing__composer">
          <Composer value="" onChange={() => {}} image={null} onImageChange={() => {}} onSubmit={() => {}} locked />
          <p className="disclaimer">AI 답변은 참고용이에요. 실제 모집 조건은 원문 공고에서 확인해 주세요.</p>
        </div>
      </div>
    </AppLayout>
  )
}
