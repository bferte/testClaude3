/**
 * Pick three random numbers between 1 and 9.
 */
export const pickNumbers = (): [number, number, number] => {
  return [
    Math.floor(Math.random() * 9) + 1,
    Math.floor(Math.random() * 9) + 1,
    Math.floor(Math.random() * 9) + 1,
  ];
};
