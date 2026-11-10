// ===== Firebase 연결 설정 =====
// 아래 값이 null 이면 "연습 모드"로 동작합니다 (글이 저장되지 않고 새로고침하면 사라짐).
// Firebase 콘솔에서 받은 설정을 넣으면 글·댓글이 실제로 저장되어 모든 학생에게 보입니다.
// 방법은 「Firebase 연결 방법.md」 참고. (이 값들은 공개되어도 괜찮은 값입니다. 보안은 firestore.rules 가 담당합니다.)
const firebaseConfig = null;
/* 예시:
const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "내프로젝트.firebaseapp.com",
  projectId: "내프로젝트",
  storageBucket: "내프로젝트.appspot.com",
  messagingSenderId: "1234567890",
  appId: "1:1234567890:web:abcdef"
};
*/

// Firebase 콘솔(Authentication)에서 만든 관리자 계정의 이메일. firestore.rules 안의 이메일과 똑같아야 합니다.
const ADMIN_EMAIL = "";
