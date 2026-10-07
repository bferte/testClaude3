import { ResultData } from "../step.types";

export function computeScore(data: ResultData) {
  const questionScore = computeQuestionsScore(data);

  const tonalScore = computeTonalScore(data);
  const vocalScore = computeVocalScore(data);
  const globalScore = Math.min(questionScore, tonalScore, vocalScore);

  return globalScore === 0 ? "bad" : globalScore === 1 ? "medium" : "good";
}

function computeQuestionsScore(data: ResultData) {
  if (!data.questions) return 2;

  const falseResponses = data.questions.filter(
    (question) => question.result === false
  ).length;

  return falseResponses > 3 ? 2 : 1;
}

function computeTonalScore(data: ResultData) {
  if (!data.tonal) return 2;
  let totalScore = 0;

  for (const item of data.tonal) {
    if (item.result[0]) totalScore += 2;
    else if (item.result[1]) totalScore += 1;
  }

  return Math.max(0, Math.min(2, Math.round(totalScore / data.tonal.length)));
}

function computeVocalScore(data: ResultData) {
  if (!data.vocal) return 2;

  const lower = Math.min(
    ...data.vocal.filter((item) => item.result).map((item) => item.rnb)
  );

  const last = data.vocal[data.vocal.length - 1].rnb;
  return last < -10 ? 2 : last < -6 ? 1 : 0;

  // return lower < -10 ? 2 : lower < -6 ? 1 : 0;
}
