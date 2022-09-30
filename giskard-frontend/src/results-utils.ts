/** 
 * If the length of s is superior at max_size, split the string into
 */
 export function abbreviateMiddle(s: string, max_length: number){
    if (max_length < 6) return s;
    let n = (max_length / 2) - 2 ;
    if (s.length > max_length)
        return s.slice (0, n) + '...' +  s.slice(-n)
    return s
}

export function maxLengthDisplayedCategory(sizeResultCard?: number){
  if (sizeResultCard! < 600) return 20
  if (sizeResultCard! < 850) return 30
  if (sizeResultCard! < 1000) return 40
  if (sizeResultCard! < 1200) return 50
  if (sizeResultCard! < 1500) return 60
  else return 70
}