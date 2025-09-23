package domains

type RepositoryInterface interface {
	QueryLLM(content string) (string, error)
}
