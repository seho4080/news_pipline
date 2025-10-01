// 댓글 데이터 모델
export class CommentModel {
  constructor(data) {
    this.id = data.id
    this.username = data.username
    this.content = data.content
    this.createdAt = data.created_at
  }
}